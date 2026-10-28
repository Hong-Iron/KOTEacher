"""코치 파이프라인: ① 검사 결과 → ② 진단 → ③ 말하기 → ④ 유출 검사 → ⑤ 전달 규칙.

①은 runner.check가 한다. 여기서는 ②~⑤를 맡는다.
"""
import ast
import os
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
        return [{"kind": "load", "msg": result["load_error"], "line": result.get("load_line")}]
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
    "3. 학생에게 할 말은 반례에서 그 줄의 값을 따라가 보게 하는 질문이다. 두 문장, 100자 안, 코드 블록 없이. 줄은 '12번 줄'처럼 실제 번호로 쓴다."
)


def context(pid, code):
    p = vault.problem(pid)
    n = 260 if "short" in EXP else 420
    return f"[문제]\n{vault.plain(p['statement_md'])[:n]}\n\n[학생 코드]\n{numbered(code)}"


ACK = "문제와 코드를 읽었습니다."
EXP = set(os.environ.get("KOTEACHER_EXP", "").split(","))  # 속도 실험: textfmt, lean, short
PROMPT = os.environ.get("KOTEACHER_PROMPT", "")  # 모델별 프로필을 억지로 고른다: qwen | en | qwen_en | mistral (견주기용, 맨 아래 PROFILES)
TEMP_DIAG, TEMP_SAY = 0.3, 0.5  # 기본(gemma) 프로필의 온도


def messages(pid, code, dynamic, task):
    pr = profile()
    if os.environ.get("KOTEACHER_SPLIT") == "0" or not pr["split"]:  # 한 덩어리 구조 (Qwen: 가짜 assistant 답 없이)
        return [{"role": "system", "content": pr["system"]},
                {"role": "user", "content": f"{context(pid, code)}\n\n{dynamic}\n\n[할 일]\n{task}"}]
    # 문제·코드는 첫 사용자 말, 증거·할 일은 둘째 사용자 말로 나눈다. 그래야 warm()이 읽힌 프롬프트가
    # 실제 프롬프트의 앞부분과 정확히 겹쳐, Ollama가 그 계산을 재사용한다 (gemma4는 기준점에서만 이어 쓸 수 있다)
    return [{"role": "system", "content": pr["system"]},
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


def trace_text(result, limit=None):
    limit = limit or (10 if "short" in EXP else 16)
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


TEXT_TASK = ("버그 줄을 찾아 아래 세 줄로만 답한다.\n줄: 버그가 있는 줄 번호 (모르면 없음)\n말: 학생에게 할 말 (규칙 3)\n"
             "분류: " + " / ".join(CATEGORIES) + " 중 하나\n"
             "줄은 오류가 난 줄이 아니라 잘못된 값이 처음 만들어진 줄이다.")


class TextStream:
    """'말: …' 줄만 글자 단위로 넘긴다 (JSON 형식을 쓰지 않을 때).
    on_line이 있으면 맨 앞의 '줄: 12'가 끝나는 즉시 줄 번호를 알린다 (말풍선을 처음부터 그 줄에 띄우려고)."""

    LINE = re.compile(r"^\s*(?:줄\s*[:：]\s*)?L?(\d+)\s*(?:번\s*줄|번)?\s*\n")

    def __init__(self, emit=None, on_line=None):
        self.emit, self.on_line, self.buf, self.pos, self.done = emit, on_line, "", None, False
        self.line_sent = on_line is None

    def feed(self, piece):
        if not self.line_sent:
            m = self.LINE.match(self.buf + piece)
            if m or "\n" in self.buf + piece:  # 첫 줄이 끝났다: 줄 번호면 알리고, 아니면 그만 본다
                self.line_sent = True
                if m:
                    self.on_line(int(m.group(1)))
        if self.done or not self.emit:
            self.buf += piece
            return
        self.buf += piece
        if self.pos is None:
            m = re.search(r"(^|\n)\s*말\s*[:：]\s*", self.buf)
            if not m:
                return
            self.pos = m.end()
        end = self.buf.find("\n", self.pos)
        chunk = self.buf[self.pos:end if end >= 0 else len(self.buf)]
        if end >= 0:
            self.done = True
        self.pos += len(chunk)
        if not getattr(self, "started", False):
            chunk = chunk.lstrip()
            self.started = bool(chunk)
        if chunk:
            self.emit(chunk)


def parse_text(text):
    g = lambda k: (re.search(rf"(^|\n)\s*{k}\s*[:：]\s*(.*)", text) or [None, None, ""])[2].strip()
    line, msg, cat = g("줄"), g("말"), g("분류")
    if not msg:  # 이름표(줄:/말:/분류:) 없이 세 줄로만 답하는 모델(Qwen 등): 순서대로 읽는다
        rows = [l.strip() for l in text.strip().splitlines() if l.strip()]
        if len(rows) >= 2 and re.fullmatch(r"(L|줄\s*)?\d+\s*(번\s*줄|번)?|없음", rows[0]):
            line = rows[0]
            last_is_cat = len(rows) >= 3 and any(c in rows[-1] for c in CATEGORIES) and len(rows[-1]) <= 20
            msg = " ".join(rows[1:-1] if last_is_cat else rows[1:])
            cat = rows[-1] if last_is_cat else cat
    ln = re.search(r"\d+", line)
    return {"line": int(ln.group()) if ln else None, "message": msg,
            "category": next((c for c in CATEGORIES if c in cat), "기타"), "cause": ""}


def diagnose_and_say(pid, code, f, result, hint_level=0, history=(), weak=(), on_message=None, on_line=None):
    dyn = evidence(f, result)
    ex = extras(pid, hint_level, history, weak)
    textfmt = "json" not in EXP  # 기본은 글 형식: JSON 문법 기호와 원인 칸을 안 써서 응답이 약 13% 빨리 끝난다
    pr = profile()
    msgs = messages(pid, code, dyn + ("\n\n" + ex if ex else ""), pr["text_task"] if textfmt else DIAG_TASK)
    try:
        if textfmt:
            stream = TextStream(on_message, on_line) if on_message or on_line else None
            text, meta = ollama.chat(msgs, max_tokens=120, temperature=pr["temp_diag"], on_token=stream.feed if stream else None,
                                     stop=None)
            d = parse_text(text)
        else:
            stream = MessageStream(on_message) if on_message else None
            schema = DIAG_SAY_SCHEMA
            if "lean" in EXP:  # 원인 칸을 빼서 생성 토큰을 줄인다
                schema = {**DIAG_SAY_SCHEMA, "properties": {k: v for k, v in DIAG_SAY_SCHEMA["properties"].items() if k != "cause"},
                          "required": ["line", "message", "category"]}
            text, meta = ollama.chat(msgs, schema=schema, max_tokens=170, temperature=pr["temp_diag"],
                                     on_token=stream.feed if stream else None)
            d = json.loads(text)
    except Exception as e:
        return {"tier": "none", "fact": f, "error": str(e)[:200]}
    n = len(code.splitlines())
    line = d.get("line") if isinstance(d.get("line"), int) and 1 <= d["line"] <= n else None
    diag = {"tier": "llm", "category": d.get("category", "기타"), "line": line,
            "lesson": "", "secret": d.get("cause", ""), "confidence": "추정", "fact": f, "meta": meta}
    msg = fill_line(tidy(d.get("message") or ""), line)
    if pr["polish"]:
        msg = pr["polish"](msg, line)
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

SAY_TASK = ("학생에게 할 말만 쓴다(머리말·따옴표 없이). '테스트로 확인한 문제 줄'을 짚되 무엇을 바꿀지는 말하지 않는다.")


class RawStream:
    """모델 출력을 그대로 넘기되, 모델이 '말:' 같은 머리말을 붙이면 뗀다."""

    def __init__(self, emit):
        self.emit, self.head, self.started = emit, "", False

    def feed(self, piece):
        if self.started:
            self.emit(piece)
            return
        self.head += piece
        if len(self.head) < 4 and not self.head.endswith((" ", "\n")):
            return
        text = re.sub(r"^\s*(말|message)\s*[:：]\s*", "", self.head).lstrip()
        if text:
            self.started = True
            self.emit(text)


def clean_raw(text):
    return tidy(re.sub(r"^\s*(말|message)\s*[:：]\s*", "", text.strip()).strip('"“” '))


def say(pid, code, diag, hint_level=0, history=(), weak=(), on_message=None):
    """말하기 + 유출 검사. 실패하면 정해진 문장."""
    if diag.get("said"):
        return diag["said"]
    f = diag["fact"]
    dyn = evidence(f, None, code, diag.get("line")) + f"\n실수 분류: {diag['category']}"
    ex = extras(pid, hint_level, history, weak)
    pr = profile()
    msgs = messages(pid, code, dyn + ("\n\n" + ex if ex else ""), pr["say_task"])
    meta, tries = {}, 0
    for tries in (1, 2):
        stream = RawStream(on_message) if (on_message and tries == 1) else None
        try:
            text, meta = ollama.chat(msgs, max_tokens=110, temperature=pr["temp_say"], on_token=stream.feed if stream else None)
            msg = fill_line(clean_raw(text), diag.get("line"))
            if pr["polish"]:
                msg = pr["polish"](msg, diag.get("line"))
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
    if ollama.external():  # 외부 API에서는 요청 한 번이 요금이므로 미리 읽히지 않는다
        return
    try:
        # messages()의 앞 두 말까지만 읽힌다. 코치의 답 자리에서 끝나므로 실제 호출이 여기서 이어 쓴다
        ollama.chat([{"role": "system", "content": profile()["system"]}, {"role": "user", "content": context(pid, code)}], max_tokens=1)
    except Exception:
        pass


_TEX = {r"\\times": "×", r"\\cdot": "·", r"\\le(q)?": "≤", r"\\ge(q)?": "≥", r"\\neq": "≠", r"\\ne\b": "≠",
        r"\\to": "→", r"\\ldots|\\dots": "…", r"\\lfloor|\\rfloor": "", r"\\left|\\right": ""}


def plain_math(msg):
    """모델이 쓴 수식 문법($k$, \\pmod{16}, \\frac{a}{b})을 말풍선에서 읽히는 평범한 글로 바꾼다."""
    msg = re.sub(r"\\pmod\{([^}]*)\}", r"mod \1", msg)
    msg = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"\1/\2", msg)
    msg = re.sub(r"\\(?:text|mathrm|operatorname)\{([^}]*)\}", r"\1", msg)
    for k, v in _TEX.items():
        msg = re.sub(k, v, msg)
    msg = re.sub(r"\$\$?([^$]{1,80}?)\$\$?", r"\1", msg)  # $k$ → k
    return msg.replace("\\", "")


def tidy(msg):
    """추적표 표기(L12)를 '12번 줄'로, 백틱과 수식 문법을 지운다."""
    msg = re.sub(r"(?<![A-Za-z0-9_])L(\d+)(?!\d)", r"\1번 줄", msg.strip())
    return plain_math(msg.replace("`", ""))


# ---------------------------------------------------------------- ④ 유출 검사

_ref_cache = {}


def _reference_lines(pid):
    if pid not in _ref_cache:
        f = next(config.PRACTICE.glob(f"*_{pid}_p1.py"), None)
        src = f.read_text(encoding="utf-8").split('if __name__')[0] if f else ""
        _ref_cache[pid] = [re.sub(r"\s+", " ", l.strip()) for l in src.splitlines() if len(l.strip()) >= 18]
    return _ref_cache[pid]


CODEY = re.compile(r"(```|^\s*(def|for|while|if|return)\b.*:|\w+\s*\[.*\]\s*=)", re.M)
# 고칠 곳을 대놓고 말하기 (2026-10-27 Ministral 답을 읽다가 찾은 구멍: "give[i][j - 1] 대신 give[i][j]를 사용해야…",
# "8번 줄의 초기값을 바꿔야 할 것 같습니다"는 고칠 값 목록과 겹치지 않아 그동안 걸러지지 않았다)
REPLACE_WITH = re.compile(r"대신\s*[A-Za-z0-9_\[\]()=<>+\-*/%. ]{0,20}?[\[\]()=<>+\-*/%]")  # 'A 대신 B'의 B가 코드(기호가 든 짧은 영문·숫자)
FIX_TOLD = re.compile(r"((바꿔|고쳐|수정해|변환해|변경해|사용해|적용해|처리해|추가해|써|넣어|빼)야\s*(합니다|해요|한다|할 것 같|하겠|됩니다|돼요|해\b)"
                      r"|(바꾸|고치|쓰)면\s*(됩니다|돼요|된다))")


def fix_said(msg):
    """고칠 코드나 고칠 곳을 단정해 말했으면 그 까닭. 질문 문장 안의 '~해야 하는지'는 괜찮다."""
    if REPLACE_WITH.search(msg):
        return "고칠 코드를 말함"
    for s in re.split(r"(?<=[.?!。])\s+|\n", msg):
        if s.strip() and not s.strip().endswith("?") and FIX_TOLD.search(s):
            return "고칠 곳을 말함"
    return None


def leak_reason(msg, diag, pid):
    if not msg:
        return "빈 답"
    if len(msg) > 320:
        return "너무 김"
    if CODEY.search(msg):
        return "코드가 들어 있음"
    told = fix_said(msg)
    if told:
        return told
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


# ---------------------------------------------------------------- Qwen에 맞춘 지시문 (KOTEACHER_PROMPT=qwen)
# 기본 지시문은 gemma의 답을 보며 다듬었다. Qwen 3.5는 (1) 이름표를 빼고 답하고, (2) 질문 대신 원인을 단정하고,
# (3) '14 번 줄'처럼 띄어 쓰는 버릇이 있어, 형식을 예시 하나로 못 박고 금지·요구를 짧은 항목으로 나눈다.
# 가짜 assistant 답(ACK) 없이 한 덩어리로 보내고, Qwen 권장값대로 온도를 0.7로 둔다 (낮으면 같은 말을 되풀이하기 쉽다).
QWEN_SYSTEM = (
    "당신은 한국 대학생의 코딩 테스트 연습을 돕는 코치입니다. 자연스러운 한국어 존댓말(~요)로 말합니다.\n"
    "반드시 지킬 것:\n"
    "1. 정답 코드, 고칠 연산자, 고칠 값은 절대 말하지 않습니다.\n"
    "2. 주어진 증거(실패한 입력, 실행 추적)에서만 출발합니다. 증거에 없는 버그를 지어내지 않습니다.\n"
    "3. 학생에게 하는 말은 질문으로 끝냅니다. 원인을 단정하지 말고, 그 줄에서 값이 어떻게 바뀌는지 학생이 직접 따라가 보게 묻습니다. "
    "두 문장, 100자 이내. 코드 블록, 마크다운, 수식 기호, 영어 문장을 쓰지 않습니다.\n"
    "4. 줄은 '7번 줄'처럼 쓰고, 숫자 뒤 조사는 붙여 씁니다('n이 2가', '7번 줄에서')."
)
QWEN_TEXT_TASK = (
    "아래 형식 그대로 세 줄만 출력합니다. 각 줄은 반드시 이름표(줄:, 말:, 분류:)로 시작합니다. 다른 말은 쓰지 않습니다.\n"
    "줄: <잘못된 값이 처음 만들어진 줄 번호, 모르면 없음>\n"
    "말: <학생에게 하는 질문>\n"
    "분류: <" + " / ".join(CATEGORIES) + " 중 하나>\n"
    "버그 줄은 오류가 난 줄이 아니라, 실행 추적에서 값이 처음 어긋나는 줄입니다.\n\n"
    "출력 예시:\n"
    "줄: 6\n"
    "말: 6번 줄에서 i가 마지막 값일 때 arr[i + 1]은 어디를 가리킬까요? 반례 [3]으로 한번 따라가 보세요.\n"
    "분류: 인덱스"
)
QWEN_SAY_TASK = (
    "학생에게 하는 질문 한 개만 씁니다(이름표, 머리말, 따옴표 없이). '테스트로 확인한 문제 줄'을 짚되 무엇을 바꿀지는 말하지 않습니다.\n"
    "예시: 9번 줄의 조건은 n이 2일 때 참일까요, 거짓일까요? 반례 2로 따라가 보세요."
)


# ---------------------------------------------------------------- 영어 지시문 (KOTEACHER_PROMPT=en | qwen_en)
# 규칙과 할 일은 영어로, 학생에게 할 말만 한국어로. 출력 이름표(줄:/말:/분류:)는 앱이 읽으므로 한국어 그대로 둔다.
# en은 대화 구조·온도를 기본 그대로 두어 언어 효과만 본다. qwen_en은 Qwen 구조(한 덩어리, 온도 0.7)를 더한다.
EN_SYSTEM = (
    "You are a coding-test practice coach for Korean university students.\n"
    "Rules:\n"
    "1. Never reveal the correct code, or which operator or value to change.\n"
    "2. Start only from the given evidence (failing input, execution trace). Never invent bugs that are not in the evidence.\n"
    "3. What you say to the student must be a question in natural, polite Korean (해요체, ending with ~요?). "
    "Do not state the cause; ask the student to trace how the values change on that line with the counterexample. "
    "At most two sentences and under 100 Korean characters. No code blocks, markdown, LaTeX, or English sentences.\n"
    "4. Refer to lines as '12번 줄' with the real line number. Use standard Korean spacing: "
    "attach particles directly to numbers and words ('12번 줄에서', 'n이 2일 때')."
)
EN_TEXT_TASK = (
    "Find the line where the wrong value is FIRST created (not the line where the error was raised): "
    "the first point where the values diverge in the execution trace.\n"
    "Output exactly these three lines with these Korean labels, and nothing else:\n"
    "줄: <line number, or 없음 if unknown>\n"
    "말: <your question to the student, in Korean>\n"
    "분류: <one of: " + " / ".join(CATEGORIES) + ">\n\n"
    "Example:\n"
    "줄: 6\n"
    "말: 6번 줄에서 i가 마지막 값일 때 arr[i + 1]은 어디를 가리킬까요? 반례 [3]으로 한번 따라가 보세요.\n"
    "분류: 인덱스"
)
EN_SAY_TASK = (
    "Write only your single question to the student, in Korean (no label, no preface, no quotes). "
    "Point at the line confirmed by the tests ('테스트로 확인한 문제 줄'), but never say what to change.\n"
    "Example: 9번 줄의 조건은 n이 2일 때 참일까요, 거짓일까요? 반례 2로 따라가 보세요."
)


# ---------------------------------------------------------------- Ministral에 맞춘 지시문 (KOTEACHER_PROMPT=mistral)
# Mistral은 시스템 프롬프트에 쓰이는 환경과 쓰임새를 분명히 적고 온도를 0.1 아래로 두라고 권한다(Ministral 3 8B 모델 카드).
# 기본 지시문으로 재 보니(2026-10-27) 말이 길고(151자) 질문 대신 고칠 곳을 설명해서, 앱과 코치의 자리를 먼저 밝히고
# '질문 하나'와 출력 형식을 못 박는다. 규칙은 영어, 학생에게 할 말과 이름표는 한국어. 구조(가짜 assistant 답)는 기본 그대로.
MI_SYSTEM = (
    "You are the coach inside KOTEacher, a desktop app where Korean university students practice coding-test problems in Python.\n"
    "The app runs the student's code on test cases and gives you the evidence: the failing input, the expected and actual output, "
    "and an execution trace.\n\n"
    "# GOAL\n"
    "Help the student find the bug by themselves. You are a tutor, not a fixer.\n\n"
    "# RULES\n"
    "1. Never reveal the correct code, the fix, or which operator or value to change. Do not explain the cause. "
    "Never write 'A 대신 B' or '~해야 해요' about the code.\n"
    "2. Use only the given evidence. Never invent bugs. State only facts you can see in the code, the failing input, or the trace "
    "(for example, the type of a value); if you are not sure, ask instead of asserting.\n"
    "3. Your message to the student is exactly ONE question in natural, polite Korean (해요체), ending with '?'. "
    "It asks the student to trace the values on the suspicious line with the counterexample. Under 80 Korean characters. "
    "No code blocks, markdown, bold, LaTeX, or English.\n"
    "4. Write lines as '12번 줄' with the real line number, and attach Korean particles directly ('12번 줄에서')."
)
MI_TEXT_TASK = (
    "Find the line where the wrong value is FIRST created (the first point where the values diverge in the execution trace), "
    "not the line where an error was raised.\n"
    "Output exactly these three lines with these Korean labels, and nothing else:\n"
    "줄: <line number, or 없음 if unknown>\n"
    "말: <ONE question to the student in Korean, ending with '?'>\n"
    "분류: <one of: " + " / ".join(CATEGORIES) + ">\n\n"
    "Example:\n"
    "줄: 6\n"
    "말: 6번 줄에서 i가 마지막 값일 때 arr[i + 1]은 어디를 가리킬까요?\n"
    "분류: 인덱스"
)
MI_SAY_TASK = (
    "Write only ONE question to the student in Korean, ending with '?' (no label, preface, quotes, or explanation). "
    "The evidence gives the line confirmed by the tests; refer to it by its number like '9번 줄' (do not copy the evidence label). "
    "Never say what to change.\n"
    "Example: 9번 줄의 조건은 n이 2일 때 참일까요, 거짓일까요?"
)


# ---------------------------------------------------------------- 모델별 프로필
# 지시문·온도·대화 구조·말 다듬기는 모델 계열마다 버릇이 달라 따로 둔다. 기본(gemma)은 gemma4 e4b의 답을 보며 다듬은 것이다.
# 지금 쓰는 모델 이름으로 고르고(profile_name), 견주기에서는 KOTEACHER_PROMPT로 억지로 고를 수 있다.
# split: 문제·코드와 증거·할 일을 두 사용자 말로 나눈다(앞부분 계산 재사용). Qwen은 가짜 assistant 답 없이 한 덩어리가 낫다.


def fill_line(msg, line=None):
    """모델이 증거의 이름표('테스트로 확인한 문제 줄')를 그대로 베끼면 실제 줄 번호로 바꾼다."""
    return re.sub(r"'?테스트로 확인한 문제 줄'?", f"{line}번 줄", msg) if line else msg


def polish_mistral(msg, line=None):
    """Ministral 말 다듬기: 굵은 글씨·따옴표를 지우고, 첫 질문 뒤에 덧붙인 설명은 버린다(규칙은 질문 하나)."""
    msg = re.sub(r"\*\*|__", "", msg).strip().strip('"“”\'')
    q = msg.find("?")
    if 0 <= q < len(msg) - 1:
        msg = msg[:q + 1]
    return " ".join(fill_line(msg, line).split())


def plain_answer_mistral(msg):
    """Ministral의 묻기·문서 답: 굵은 글씨와 제목 표시(#)를 지운다 (말풍선은 글자만 보인다)."""
    return re.sub(r"^\s*#+\s*", "", re.sub(r"\*\*|__", "", msg), flags=re.M).strip()


# temp_ask·answer: 학생이 직접 물은 답(코드 묻기·문서 질문)의 온도와 다듬기
PROFILES = {
    "gemma": {"system": SYSTEM, "text_task": TEXT_TASK, "say_task": SAY_TASK, "temp_diag": TEMP_DIAG, "temp_say": TEMP_SAY,
              "temp_ask": 0.4, "split": True, "polish": None, "answer": None},
    "qwen": {"system": QWEN_SYSTEM, "text_task": QWEN_TEXT_TASK, "say_task": QWEN_SAY_TASK, "temp_diag": 0.7, "temp_say": 0.7,
             "temp_ask": 0.7, "split": False, "polish": None, "answer": None},
    "en": {"system": EN_SYSTEM, "text_task": EN_TEXT_TASK, "say_task": EN_SAY_TASK, "temp_diag": TEMP_DIAG, "temp_say": TEMP_SAY,
           "temp_ask": 0.4, "split": True, "polish": None, "answer": None},
    "qwen_en": {"system": EN_SYSTEM, "text_task": EN_TEXT_TASK, "say_task": EN_SAY_TASK, "temp_diag": 0.7, "temp_say": 0.7,
                "temp_ask": 0.7, "split": False, "polish": None, "answer": None},
    # Mistral 권장: 쓰임새를 시스템 프롬프트에 분명히, 온도 0.1 아래 (Ministral 3 8B 모델 카드)
    "mistral": {"system": MI_SYSTEM, "text_task": MI_TEXT_TASK, "say_task": MI_SAY_TASK, "temp_diag": 0.05, "temp_say": 0.05,
                "temp_ask": 0.05, "split": True, "polish": polish_mistral, "answer": plain_answer_mistral},
}


def clean_answer(msg):
    """묻기·문서 답을 지금 모델의 버릇에 맞춰 다듬는다."""
    fn = profile()["answer"]
    return fn(msg) if fn else msg


def profile_name():
    if PROMPT in PROFILES:
        return PROMPT
    m = ((config.api_conf().get("model") if ollama.external() else config.MODEL) or "").lower()
    if "mistral" in m:  # Ministral도 이름에 mistral이 들어간다
        return "mistral"
    if "qwen" in m or "omnicoder" in m:  # OmniCoder-9B는 Qwen3.5-9B를 코딩용으로 다듬은 것이라 Qwen 버릇이 같다
        return "qwen"
    return "gemma"


def profile():
    return PROFILES[profile_name()]
