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


def is_stub(code):
    """아직 풀이라고 할 게 없는 코드 (템플릿 그대로, 본문 두 문장 이하)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "solution"), None)
    if fn is None:
        return True
    stmts = [n for n in ast.walk(fn) if isinstance(n, ast.stmt)] [1:]
    return len(stmts) <= 2


# ---------------------------------------------------------------- 복잡도 어림 (AST)

SIZE_WORD = re.compile(r"(개|명|글자|칸|줄|쌍|길이|개수|크기|원소)")


def limits_n(statement_md):
    """문제 제한에서 입력 '크기'의 최댓값을 어림한다 (예: '보석 1~100,000개' → 100000).
    '숫자 1~200,000,000'처럼 값의 범위는 크기가 아니므로 뺀다."""
    best = None
    for line in statement_md.splitlines():
        for m in re.finditer(r"~\s*([\d,]{2,})\s*(\S{0,3})", line):
            n = int(m.group(1).replace(",", ""))
            before = re.split(r"[,·/(;]", line[:m.start()])[-1]  # 같은 줄의 앞 제한은 보지 않는다
            if SIZE_WORD.search(m.group(2)) or SIZE_WORD.search(before):
                best = max(best or 0, n)
    return best


def loop_depth(code):
    """for와 내포(comprehension)만 센다. while은 이분 탐색·두 포인터처럼 n번보다 적게 도는 일이 많다."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    def depth(node):
        best = 0
        for c in ast.iter_child_nodes(node):
            d = depth(c)
            if isinstance(c, (ast.For, ast.comprehension)):
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

def numbered(code):
    return "\n".join(f"{i:>3}| {l}" for i, l in enumerate(code.splitlines(), 1))


# 프롬프트를 처음 읽는 속도는 초당 약 100토큰(M3 16GB)이라 프롬프트를 짧게 쓴다. 앞부분이 같은 프롬프트는
# Ollama가 계산을 재사용하므로(10초 → 1초 안팎), 모든 호출이 같은 규칙·문제·코드로 시작하게 하고 바뀌는 것은 뒤에 둔다.
SYSTEM = (
    "너는 코딩 테스트 연습 코치다. 부드러운 존댓말.\n"
    "1. 정답 코드나 바꿀 연산자·값을 학생에게 말하지 않는다.\n"
    "2. 증거에서 출발하고 증거에 없는 버그를 지어내지 않는다.\n"
    "3. message: 반례에서 그 줄의 값을 따라가 보게 하는 질문. 두 문장, 100자 안, 코드 블록 없이. 줄은 'N번 줄'로 쓴다."
)


def context(pid, code):
    p = vault.problem(pid)
    return f"[문제]\n{vault.plain(p['statement_md'])[:420]}\n\n[학생 코드]\n{numbered(code)}"


ACK = "문제와 코드를 읽었습니다."


def messages(pid, code, dynamic, task):
    # 문제·코드는 첫 사용자 말, 증거·할 일은 둘째 사용자 말로 나눈다. 그래야 warm()이 읽힌 프롬프트가
    # 실제 프롬프트의 앞부분과 정확히 겹쳐, Ollama가 그 계산을 재사용한다 (gemma4는 기준점에서만 이어 쓸 수 있다)
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": context(pid, code)},
            {"role": "assistant", "content": ACK},
            {"role": "user", "content": f"{dynamic}\n\n[할 일]\n{task}"}]


def evidence(f, result=None, code=None, line=None):
    ev = [f"[증거] {f.get('where', '')}에서 실패. 입력: {f.get('args')}"]
    if f.get("expected") is not None and f.get("kind") == "wrong":
        ev.append(f"기대: {f.get('expected')} / 내 답: {f.get('got')}")
    elif f.get("kind") == "timeout":
        ev.append("결과: 시간 제한을 넘김 (무한 루프이거나 너무 느림)")
    elif f.get("msg"):
        ev.append(f"오류: {f.get('msg')}" + (f" ({f.get('line')}번 줄)" if f.get("line") else ""))
    if line and code:
        ev.append(f"테스트로 확인한 문제 줄: {line}번 줄 `{code.splitlines()[line - 1].strip()}`")
    tt = trace_text(result)
    if tt:
        ev.append(f"[실행 추적] L번호: 그 줄 실행 뒤 바뀐 변수\n{tt}")
    return "\n".join(ev)


def extras(pid, hint_level, history, weak):
    out = []
    hc = _hint_context(pid, hint_level)
    if hc:
        out.append(f"[학생이 이미 연 힌트]\n{hc}")
    if weak:
        out.append("[이 학생이 자주 틀리는 분류] " + ", ".join(w["category"] for w in weak))
    if history:
        out.append("[코치가 이미 한 말. 되풀이하지 말 것]\n" + "\n".join(f"- {h}" for h in list(history)[-2:]))
    return "\n\n".join(out)


def _hint_context(pid, hint_level):
    if hint_level <= 0:
        return ""
    lad = vault.hint_ladder(pid)
    return "\n".join(f"- {l['title']}: {l['text'][:500]}" for l in lad[:min(hint_level, vault.HINTS)])


def trace_text(result, limit=16):
    """짧은 형식: 'L12 s='F'' (12번 줄을 실행한 뒤 바뀐 변수). 프롬프트를 짧게 해 읽는 시간을 줄인다."""
    rows = (result or {}).get("trace") or []
    out = []
    for r in rows[:limit]:
        vs = " ".join(f"{k}={v}" for k, v in r["vars"].items())
        out.append(f"L{r['line']} {vs}" + (f" ret={r['ret']}" if r.get("ret") else ""))
    if len(rows) > limit:
        out.append("…")
    return "\n".join(out)


class MessageStream:
    """JSON으로 생성되는 답에서 "message" 값만 글자 단위로 꺼내 넘긴다."""

    def __init__(self, emit):
        self.emit, self.buf, self.pos, self.done = emit, "", None, False

    def feed(self, piece):
        if self.done:
            return
        self.buf += piece
        if self.pos is None:
            m = re.search(r'"message"\s*:\s*"', self.buf)
            if not m:
                return
            self.pos = m.end()
        out, i = [], self.pos
        while i < len(self.buf):
            c = self.buf[i]
            if c == "\\":
                if i + 1 >= len(self.buf):
                    break
                nxt = self.buf[i + 1]
                out.append({"n": "\n", "t": " ", '"': '"', "\\": "\\"}.get(nxt, nxt))
                i += 2
                continue
            if c == '"':
                self.done = True
                i += 1
                break
            out.append(c)
            i += 1
        self.pos = i
        if out:
            self.emit("".join(out))


# ---------------------------------------------------------------- ② 진단

def diagnose(pid, code, result, fs, llm=True, **say_kw):
    """확실한 것부터: 수리 검색 → 오류 줄 → AI 진단(말하기까지 한 번에)."""
    if not fs:
        return None
    f = fs[0]
    if f["kind"] in ("syntax", "load", "fatal"):
        return {"tier": "rule", "category": "예외", "line": f.get("line"), "lesson": "", "secret": None,
                "confidence": "확인됨", "fact": f}
    rep = result.get("repair") or {}
    if rep.get("fixes"):  # 한 군데 수정으로 전부 통과하면 그 줄이 가장 믿을 만하다
        fx = rep["fixes"][0]
        return {"tier": "repair", "category": fx["category"], "line": fx["line"], "lesson": "",
                "secret": fx["label"], "confidence": "확인됨", "fact": f, "fix": fx}
    # 오류는 오류 난 줄과 원인 줄이 다른 일이 많다(2군데 버그에서 50%). 수리로 안 고쳐지면 AI가 추적표로 원인 줄을 찾는다
    rule = {"tier": "rule", "category": {"timeout": "복잡도", "error": "예외"}.get(f["kind"], "기타"),
            "line": f.get("line") if f["kind"] == "error" else None, "lesson": "", "secret": None,
            "confidence": "확인됨" if f["kind"] in ("timeout", "error") else "추정", "fact": f}
    if not llm:
        return rule
    d = diagnose_and_say(pid, code, f, result, **say_kw)
    if d["tier"] == "none":
        return rule
    if f["kind"] == "timeout" and d["category"] not in ("복잡도", "조건 놓침", "비교·경계", "초기값"):
        d["category"] = "복잡도"
    return d


DIAG_SAY_SCHEMA = {
    "type": "object",
    "properties": {
        "line": {"type": ["integer", "null"]},
        "message": {"type": "string"},
        "category": {"type": "string", "enum": CATEGORIES},
        "cause": {"type": "string"},
    },
    "required": ["line", "message", "category", "cause"],
}

DIAG_TASK = ("버그 줄을 찾아 JSON으로: line, message(학생에게, 규칙 3), category, cause(원인 20자, 학생에게 안 보임).\n"
             "line은 오류가 난 줄이 아니라 잘못된 값이 처음 만들어진 줄이다. 실행 추적에서 값이 처음 어긋나는 곳을 찾는다. 모르면 null.")


def diagnose_and_say(pid, code, f, result, hint_level=0, history=(), weak=(), on_message=None):
    dyn = evidence(f, result)
    ex = extras(pid, hint_level, history, weak)
    msgs = messages(pid, code, dyn + ("\n\n" + ex if ex else ""), DIAG_TASK)
    stream = MessageStream(on_message) if on_message else None
    try:
        text, meta = ollama.chat(msgs, schema=DIAG_SAY_SCHEMA, max_tokens=170, temperature=0.3,
                                 on_token=stream.feed if stream else None)
        d = json.loads(text)
    except Exception as e:
        return {"tier": "none", "fact": f, "error": str(e)[:200]}
    n = len(code.splitlines())
    line = d.get("line") if isinstance(d.get("line"), int) and 1 <= d["line"] <= n else None
    diag = {"tier": "llm", "category": d.get("category", "기타"), "line": line,
            "lesson": "", "secret": d.get("cause", ""), "confidence": "추정", "fact": f, "meta": meta}
    msg = tidy(d.get("message") or "")
    reason = leak_reason(msg, diag, pid)
    diag["said"] = ({"kind": "question", "message": trim(msg), "source": "ai", "meta": meta, "tries": 1} if not reason
                    else {"kind": "nudge", "message": template(diag), "source": "template", "meta": meta, "tries": 1, "leak": reason})
    return diag


# ---------------------------------------------------------------- ③ 말하기

SAY_SCHEMA = {
    "type": "object",
    "properties": {"message": {"type": "string"}},
    "required": ["message"],
}

SAY_TASK = "JSON으로 message만 쓴다. '테스트로 확인한 문제 줄'을 짚되 무엇을 바꿀지는 말하지 않는다."


def say(pid, code, diag, hint_level=0, history=(), weak=(), on_message=None):
    """말하기 + 유출 검사. 실패하면 정해진 문장."""
    if diag.get("said"):
        return diag["said"]
    f = diag["fact"]
    dyn = evidence(f, None, code, diag.get("line")) + f"\n실수 분류: {diag['category']}"
    ex = extras(pid, hint_level, history, weak)
    msgs = messages(pid, code, dyn + ("\n\n" + ex if ex else ""), SAY_TASK)
    meta, tries = {}, 0
    for tries in (1, 2):
        stream = MessageStream(on_message) if (on_message and tries == 1) else None
        try:
            text, meta = ollama.chat(msgs, schema=SAY_SCHEMA, max_tokens=120, temperature=0.5,
                                     on_token=stream.feed if stream else None)
            msg = tidy(json.loads(text).get("message", ""))
        except Exception as e:
            meta = {"error": str(e)[:200]}
            break
        reason = leak_reason(msg, diag, pid)
        if not reason:
            return {"kind": "question", "message": trim(msg), "source": "ai", "meta": meta, "tries": tries}
        msgs = msgs + [{"role": "assistant", "content": text},
                       {"role": "user", "content": f"규칙 위반({reason}). 고치는 법을 빼고 질문으로 다시 써라."}]
    return {"kind": "nudge", "message": template(diag), "source": "template", "meta": meta, "tries": tries}


def warm(pid, code):
    """문제를 열 때 공통 앞부분(규칙·문제·코드)을 미리 읽혀 둔다. 첫 코치 응답이 빨라진다."""
    try:
        # messages()의 앞 두 말까지만 읽힌다. 코치의 답 자리에서 끝나므로 실제 호출이 여기서 이어 쓴다
        ollama.chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": context(pid, code)}], max_tokens=1)
    except Exception:
        pass


def tidy(msg):
    """추적표 표기(L12)를 '12번 줄'로, 백틱을 지운다."""
    msg = re.sub(r"(?<![A-Za-z0-9_])L(\d+)(?!\d)", r"\1번 줄", msg.strip())
    return msg.replace("`", "")


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
