"""코치 파이프라인: ① 검사 결과 → ② 진단 → ③ 말하기 → ④ 유출 검사 → ⑤ 전달 규칙.

①은 runner.check가 한다. 여기서는 ②~⑤를 맡는다.
"""
import ast
import json
import re
import time

from . import ollama, vault, config

CATEGORIES = ["비교·경계", "초기값", "인덱스", "자료구조", "복잡도", "조건 놓침", "빈 입력", "예외", "기타"]

# ---------------------------------------------------------------- ① 사실 정리

def facts(result):
    """검사 결과에서 실패 사실을 뽑는다. 가장 중요한 것이 앞에 온다."""
    out = []
    if result.get("fatal"):
        return [{"kind": "fatal", "msg": result["fatal"]}]
    if result.get("syntax"):
        s = result["syntax"]
        return [{"kind": "syntax", "line": s["line"], "msg": s["msg"]}]
    if result.get("load_error"):
        return [{"kind": "load", "msg": result["load_error"]}]
    for i, e in enumerate(result.get("examples", [])):
        if e.get("skipped") or e.get("ok"):
            continue
        if e.get("timeout"):
            out.append({"kind": "timeout", "where": f"예시 {i + 1}", "args": e["args"]})
        elif e.get("error"):
            out.append({"kind": "error", "where": f"예시 {i + 1}", "args": e["args"], "msg": e["error"], "line": e.get("line")})
        else:
            out.append({"kind": "wrong", "where": f"예시 {i + 1}", "args": e["args"], "expected": e["expected"], "got": e.get("got")})
    ff = (result.get("hidden") or {}).get("first_fail")
    if ff:
        k = "timeout" if ff.get("timeout") else "error" if ff.get("error") else "wrong"
        out.append({"kind": k, "where": "숨은 검사", "args": ff["args"], "expected": ff["expected"],
                    "got": ff.get("got"), "msg": ff.get("error"), "line": ff.get("line")})
    # 반례는 가장 작은 입력이 가르치기 좋다
    out.sort(key=lambda f: (f["kind"] != "error", f["kind"] != "wrong", len(f.get("args", ""))))
    return out


def passed(result):
    ex = result.get("examples") or []
    hid = result.get("hidden") or {}
    return bool(ex) and all(e.get("ok") for e in ex) and hid.get("first_fail") is None and hid.get("run", 0) == hid.get("total", 0)


# ---------------------------------------------------------------- 복잡도 어림 (AST)

def limits_n(statement_md):
    """문제 제한에서 가장 큰 크기를 어림한다 (예: '보석 1~100,000개' → 100000)."""
    nums = [int(x.replace(",", "")) for x in re.findall(r"~\s*([\d,]{4,})", statement_md)]
    nums += [10 ** int(x) for x in re.findall(r"10\^(\d+)", statement_md)]
    return max(nums) if nums else None


def loop_depth(code):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    def depth(node):
        best = 0
        for c in ast.iter_child_nodes(node):
            d = depth(c)
            if isinstance(c, (ast.For, ast.While, ast.comprehension)):
                d += 1
            best = max(best, d)
        return best
    return depth(tree)


def complexity_risk(code, statement_md):
    n, d = limits_n(statement_md), loop_depth(code)
    if not n or d is None or d < 2:
        return None
    ops = n ** d
    if ops > 2e8:
        return {"depth": d, "n": n, "ops": ops}
    return None


# ---------------------------------------------------------------- ② 진단

DIAG_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
        "line": {"type": ["integer", "null"]},
        "cause": {"type": "string"},
        "lesson": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["category", "line", "cause", "lesson", "confidence"],
}


def numbered(code):
    return "\n".join(f"{i:>3}| {l}" for i, l in enumerate(code.splitlines(), 1))


def diagnose(pid, code, result, fs):
    """확실한 것부터: 오류 줄 → 수리 검색 → AI 진단."""
    if not fs:
        return None
    f = fs[0]
    if f["kind"] in ("syntax", "load", "fatal"):
        return {"tier": "rule", "category": "예외", "line": f.get("line"), "lesson": "", "secret": None,
                "confidence": "확인됨", "fact": f}
    if f["kind"] == "timeout":
        return {"tier": "rule", "category": "복잡도", "line": None, "lesson": "", "secret": None,
                "confidence": "확인됨", "fact": f}
    if f["kind"] == "error" and f.get("line"):
        return {"tier": "rule", "category": "예외", "line": f["line"], "lesson": "", "secret": None,
                "confidence": "확인됨", "fact": f}
    rep = result.get("repair") or {}
    if rep.get("fixes"):
        fx = rep["fixes"][0]
        return {"tier": "repair", "category": fx["category"], "line": fx["line"], "lesson": "",
                "secret": fx["label"], "confidence": "확인됨", "fact": f, "fix": fx}
    return llm_diagnose(pid, code, f)


def llm_diagnose(pid, code, f):
    p = vault.problem(pid)
    sys = ("너는 코딩 테스트 채점 보조다. 학생 코드가 반례에서 왜 틀리는지 찾는다. "
           "반드시 아래 증거에서 출발한다. 증거로 설명되지 않는 버그를 지어내지 않는다. "
           "cause는 원인을 한 문장으로, lesson은 학생이 배워야 할 점을 고치는 법 없이 한 문장으로 쓴다. "
           "줄 번호는 코드 왼쪽 숫자를 쓴다. 모르겠으면 line은 null, confidence는 0.3 이하.")
    user = (f"[문제]\n{vault.plain(p['statement_md'])[:700]}\n\n"
            f"[증거] {f['where']}에서 틀림. 입력: {f.get('args')}\n기대: {f.get('expected')}\n내 답: {f.get('got') or f.get('msg')}\n\n"
            f"[코드]\n{numbered(code)}")
    try:
        text, meta = ollama.chat([{"role": "system", "content": sys}, {"role": "user", "content": user}],
                                 schema=DIAG_SCHEMA, max_tokens=300, temperature=0.2)
        d = json.loads(text)
    except Exception as e:
        return {"tier": "none", "category": "기타", "line": None, "lesson": "", "secret": None,
                "confidence": "추정", "fact": f, "error": str(e)[:200]}
    conf = float(d.get("confidence") or 0)
    line = d.get("line") if isinstance(d.get("line"), int) and 1 <= d["line"] <= len(code.splitlines()) else None
    return {"tier": "llm", "category": d.get("category", "기타"), "line": line if conf >= 0.5 else None,
            "lesson": d.get("lesson", ""), "secret": d.get("cause", ""), "confidence": "추정",
            "fact": f, "llm_conf": conf, "meta": meta}


# ---------------------------------------------------------------- ③ 말하기

SAY_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": ["question", "nudge", "warning"]},
        "message": {"type": "string"},
    },
    "required": ["kind", "message"],
}

SAY_RULES = (
    "너는 코딩 테스트를 연습하는 학생 옆의 선배 코치다. 반말 대신 부드러운 존댓말(~요)을 쓴다.\n"
    "규칙:\n"
    "1. 정답 코드, 고친 코드, 바꿀 연산자나 값을 말하지 않는다. 학생이 스스로 찾게 한다.\n"
    "2. [증거]에 있는 사실 하나에 대해서만 말한다. 증거에 없는 버그를 지어내지 않는다.\n"
    "3. 반례를 학생이 손으로 따라가 볼 수 있게 짚고, 질문 하나로 끝낸다.\n"
    "4. 두세 문장, 180자 안. 쉬운 한국어. 코드 블록을 쓰지 않는다.\n"
    "5. 줄을 짚을 때는 'N번 줄'이라고 쓴다."
)


def _hint_context(pid, hint_level):
    if hint_level <= 0:
        return ""
    lad = vault.hint_ladder(pid)
    return "\n".join(f"- {l['title']}: {l['text'][:500]}" for l in lad[:min(hint_level, 4)])


def speak_messages(pid, code, diag, hint_level, history, weak):
    p = vault.problem(pid)
    f = diag["fact"]
    lines = code.splitlines()
    ev = [f"{f.get('where', '')}: 입력 {f.get('args')}"]
    if f.get("expected") is not None:
        ev.append(f"기대 {f.get('expected')}, 내 답 {f.get('got') or f.get('msg')}")
    elif f.get("msg"):
        ev.append(f"오류 {f.get('msg')}")
    if diag.get("line"):
        ev.append(f"의심 줄: {diag['line']}번 줄 `{lines[diag['line'] - 1].strip()}`")
    ev.append(f"실수 분류: {diag['category']}")
    if diag.get("lesson"):
        ev.append(f"배울 점(그대로 말하지 말 것): {diag['lesson']}")
    user = f"[문제]\n{vault.plain(p['statement_md'])[:600]}\n\n[증거]\n" + "\n".join(ev)
    hc = _hint_context(pid, hint_level)
    if hc:
        user += f"\n\n[학생이 이미 연 힌트]\n{hc}"
    if weak:
        user += "\n\n[이 학생이 자주 틀리는 분류] " + ", ".join(w["category"] for w in weak)
    if history:
        user += "\n\n[코치가 이미 한 말. 되풀이하지 말 것]\n" + "\n".join(f"- {h}" for h in history[-2:])
    return [{"role": "system", "content": SAY_RULES}, {"role": "user", "content": user}]


def say(pid, code, diag, hint_level=0, history=(), weak=(), on_token=None):
    """말하기 + 유출 검사. 실패하면 정해진 문장."""
    msgs = speak_messages(pid, code, diag, hint_level, list(history), list(weak))
    meta, tries = {}, 0
    for tries in (1, 2):
        try:
            text, meta = ollama.chat(msgs, schema=SAY_SCHEMA, max_tokens=220, temperature=0.5)
            d = json.loads(text)
            msg = d.get("message", "").strip()
        except Exception as e:
            meta = {"error": str(e)[:200]}
            break
        reason = leak_reason(msg, diag, pid)
        if not reason:
            return {"kind": d.get("kind", "question"), "message": trim(msg), "source": "ai", "meta": meta, "tries": tries}
        msgs = msgs + [{"role": "assistant", "content": text},
                       {"role": "user", "content": f"규칙 위반({reason}). 고치는 법을 빼고 질문으로 다시 써라."}]
    return {"kind": "nudge", "message": template(diag), "source": "template", "meta": meta, "tries": tries}


# ---------------------------------------------------------------- ④ 유출 검사

_ref_cache = {}


def _reference_lines(pid):
    if pid not in _ref_cache:
        f = next(config.PRACTICE.glob(f"*_{pid}_p1.py"), None)
        src = f.read_text(encoding="utf-8").split('if __name__')[0] if f else ""
        _ref_cache[pid] = [re.sub(r"\s+", " ", l.strip()) for l in src.splitlines() if len(l.strip()) >= 18]
    return _ref_cache[pid]


CODEY = re.compile(r"(```|^\s*(def|for|while|if|return)\b.*:|\w+\s*\[.*\]\s*=)", re.M)


def leak_reason(msg, diag, pid):
    if not msg:
        return "빈 답"
    if len(msg) > 320:
        return "너무 김"
    if CODEY.search(msg):
        return "코드가 들어 있음"
    norm = re.sub(r"\s+", " ", msg)
    for l in _reference_lines(pid):
        if l in norm:
            return "모범 풀이 코드와 겹침"
    fx = diag.get("fix")
    if fx:
        target = fx["label"].split("→")[-1].strip()
        # '<로 바꾸', '< 를 쓰' 처럼 고칠 값을 바로 말하면 유출
        if re.search(re.escape(target) + r"\s*(으?로|를|을|이|가)?\s*(바꾸|바꿔|고치|고쳐|써|쓰|사용|넣)", msg):
            return "고칠 값을 말함"
    return None


def trim(msg, n=260):
    if len(msg) <= n:
        return msg
    cut = max(msg.rfind(". ", 0, n), msg.rfind("? ", 0, n), msg.rfind("요 ", 0, n))
    return msg[:cut + 1] if cut > 40 else msg[:n] + "…"


def template(diag):
    f, line = diag.get("fact", {}), diag.get("line")
    at = f"{line}번 줄" if line else "코드"
    if f.get("kind") == "syntax":
        return f"{f.get('line')}번 줄에서 문법 오류가 났어요: {f.get('msg')}"
    if f.get("kind") == "timeout":
        return f"{f.get('where')}에서 시간 제한을 넘겼어요. 반복이 끝나는 조건이 언젠가 꼭 참이 되는지, 입력이 커지면 몇 번 도는지 따져 보세요."
    if f.get("kind") == "error":
        return f"{f.get('where')}에서 {f.get('msg')} 오류가 났어요. {at}에서 그 값이 무엇인지 입력 {f.get('args')}로 따라가 보세요."
    base = f"입력 {f.get('args')}의 기대 답은 {f.get('expected')}, 내 답은 {f.get('got')}예요."
    tips = {"비교·경계": f"{at}의 비교가 같은 값일 때 어떻게 되는지 따라가 보세요.",
            "인덱스": f"{at}에서 인덱스가 하나 어긋나지 않는지 보세요.",
            "조건 놓침": f"{at}의 조건이 문제의 모든 경우를 덮는지 보세요."}
    return base + " " + tips.get(diag.get("category"), f"이 입력을 손으로 따라가며 {at}에서 값이 어떻게 바뀌는지 보세요.")


# ---------------------------------------------------------------- ⑤ 전달 규칙

class Policy:
    """언제 먼저 말할지. mode: quiet | normal | active"""
    AUTO_GAP = 180

    def __init__(self):
        self.last_auto = 0.0
        self.said = set()

    def decide(self, mode, trigger, diag):
        """'speak' | 'chip' | 'none'"""
        if diag is None:
            return "none"
        sig = (diag["category"], diag.get("line"), diag["fact"].get("args"))
        if diag["fact"].get("kind") == "syntax":
            return "chip"
        if mode == "quiet":
            return "chip"
        if sig in self.said:
            return "chip"
        if trigger == "idle":
            if time.time() - self.last_auto < self.AUTO_GAP:
                return "chip"
            if mode == "normal" and diag["confidence"] != "확인됨":
                return "chip"
        return "speak"

    def spoke(self, trigger, diag):
        self.said.add((diag["category"], diag.get("line"), diag["fact"].get("args")))
        if trigger == "idle":
            self.last_auto = time.time()
