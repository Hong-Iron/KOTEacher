"""코치에게 '예제 코드'를 물었을 때. 질문을 네 가지로 나눠 다르게 답한다.

  ① 문법·라이브러리 사용법, ② 디버깅용 코드  → AI가 작은 일반 예제를 쓰고, 앱이 실행해 확인한 뒤 바로 보여 준다
  ③ 알고리즘 기본 틀                      → 검증된 개념 코드(*_impl.py)의 핵심 함수를 접어서. 펼치면 힌트 1개
  ④ 이 문제의 답·고친 코드                 → 보여 주지 않고 힌트 사다리로

AI가 쓴 예제는 실행 전에 허용한 표준 모듈만 쓰는지, 파일·시스템을 건드리지 않는지 확인하고,
지금 문제의 모범 풀이와 겹치거나 solution 함수를 만들면 버린다.
"""
import ast
import re
import subprocess
import tempfile
from pathlib import Path

from . import config, vault

ANSWER = re.compile(r"정답|답\s*코드|답안|풀이\s*코드|모범\s*(답|풀이)|고친\s*코드|수정한\s*코드|전체\s*코드|완성(된|한)?\s*코드|"
                    r"어떻게\s*고쳐|고쳐\s*(줘|주세요|줄래)|(이|그)\s*문제.*(코드|풀어)\s*(줘|주세요)|답\s*(알려|보여)")
EXAMPLE = re.compile(r"예제|예시|샘플|코드\s*(로|를|좀)?\s*(보여|짜|써|알려)|(법|방법|예)\s*(좀\s*)?(보여|알려)|사용\s*법|쓰는\s*법|"
                     r"어떻게\s*(써|쓰|사용)|사용\s*예|템플릿|기본\s*(틀|형|코드)|구현\s*(해|코드|방법|법)|print.*(넣|찍)|찍어\s*보")
# 알고리즘 틀로 접어 보여 줄 개념 (번호). 정렬·딕셔너리·큐·힙 같은 라이브러리 사용법은 ① 문법 예제로 바로 보여 준다
ALGO_TEMPLATES = {"13", "14", "15", "20", "24", "25", "26", "29"}

SAFE_MODULES = {"collections", "heapq", "bisect", "itertools", "functools", "math", "re", "string", "operator",
                "datetime", "fractions", "decimal", "statistics", "typing", "dataclasses", "copy", "random", "array"}
BANNED_NAMES = {"open", "exec", "eval", "compile", "__import__", "input", "globals", "locals", "vars", "getattr",
                "setattr", "delattr", "breakpoint", "exit", "quit"}


def classify(question, sel_text=""):
    """'answer' | 'template' | 'example' | None(보통 질문). template이면 (kind, 개념) 둘을 돌려준다."""
    q = question or ""
    if ANSWER.search(q):
        return "answer", None
    if not EXAMPLE.search(q):
        return None, None
    c = match_concept(q)
    if c and c["num"] in ALGO_TEMPLATES and impl_file(c):
        return "template", c
    return "example", None


def match_concept(q):
    """질문에 나온 개념 이름·별칭으로 개념 문서를 찾는다 (가장 긴 일치)."""
    low, best = q.lower(), (0, None)
    for c in vault.concepts():
        # 제목을 '와/과'·괄호로 나눈 조각도 이름으로 본다 ('트리 순회와 이진 탐색 트리' → '트리 순회', '이진 탐색 트리')
        parts = [p.strip() for p in re.split(r"와\s|과\s|[()]", c["title"]) if p.strip()]
        names = [c["title"]] + parts + [a.strip() for a in c.get("aliases", "").split(",")]
        for n in names:
            n2 = n.lower()
            if len(n2) >= 2 and n2 in low and len(n2) > best[0]:
                best = (len(n2), c)
    return best[1]


def impl_file(c):
    return next(config.CONCEPTS.glob(f"{c['num']}_*_impl.py"), None)


def template_of(c, limit=40):
    """개념 코드의 첫 함수(핵심 구현)와 그 함수가 쓰는 import만 잘라 온다."""
    f = impl_file(c)
    src = f.read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next((n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))), None)  # 첫 함수나 클래스
    if not fn:
        return None
    body = ast.get_source_segment(src, fn)
    used = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
    imports = []
    for n in tree.body:
        if isinstance(n, ast.ImportFrom) and any(a.name in used for a in n.names):
            imports.append(f"from {n.module} import " + ", ".join(a.name for a in n.names if a.name in used))
        elif isinstance(n, ast.Import) and any(a.name in used for a in n.names):
            imports.append("import " + ", ".join(a.name for a in n.names if a.name in used))
    code = ("\n".join(imports) + "\n\n\n" if imports else "") + body
    lines = code.splitlines()
    if len(lines) > limit:  # 길면 메서드·함수 경계에서 자른다 (중간에서 자르면 실행되지 않는다)
        cut = max((i for i, l in enumerate(lines[:limit]) if re.match(r"\s{4}def |def ", l) and i > 0), default=limit)
        lines = lines[:cut] + ["    # … (개념 코드에서 앞부분만 가져왔습니다. 나머지는 개념 문서의 코드에서 볼 수 있습니다)"]
    return "\n".join(lines), f.name


def split_answer(text):
    """'설명 + ```python 코드```' → (설명, 코드)."""
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.S)
    if not m:
        return text.strip(), None
    expl = (text[:m.start()] + " " + text[m.end():]).strip()
    return expl, m.group(1).rstrip()


def unsafe(code):
    """실행하면 안 되는 코드면 이유를, 괜찮으면 None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"문법 오류: {e.msg}"
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] not in SAFE_MODULES for a in n.names):
            return "허용하지 않는 모듈"
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] not in SAFE_MODULES:
            return "허용하지 않는 모듈"
        if isinstance(n, ast.Name) and n.id in BANNED_NAMES:
            return f"쓸 수 없는 이름: {n.id}"
        if isinstance(n, ast.Attribute) and n.attr.startswith("__"):
            return "특수 속성 접근"
        if isinstance(n, ast.FunctionDef) and n.name == "solution":
            return "solution 함수를 만듦"
    return None


def overlaps_answer(code, pid):
    from .coach import _reference_lines
    norm = " ".join(re.sub(r"\s+", " ", l.strip()) for l in code.splitlines())
    return any(l in norm for l in _reference_lines(pid))


def run(code, timeout=3):
    """격리 프로세스에서 돌려 (성공?, 출력)을 돌려준다."""
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "example.py"
        f.write_text(code, encoding="utf-8")
        try:
            p = subprocess.run(config.child_cmd("run", str(f)), capture_output=True, timeout=timeout, cwd=d, **config.child_kw())
        except subprocess.TimeoutExpired:
            return False, f"{timeout}초 안에 끝나지 않았습니다"
        out = (p.stdout or "").strip()
        if p.returncode != 0:
            err = (p.stderr or "").strip().splitlines()
            return False, (err[-1] if err else "오류")[:200]
        return True, out[-600:]


EXAMPLE_TASK = ("[학생 질문] {q}\n"
                "학생이 예제 코드를 원한다. 지금 문제와 상관없는 작고 일반적인 파이썬 예제로 답한다.\n"
                "- 먼저 쉬운 말로 한두 문장 설명하고, 이어서 ```python 코드 블록 하나를 쓴다.\n"
                "- 코드는 12줄 이내, 표준 라이브러리만 쓰고, 마지막에 print로 결과를 보여 준다.\n"
                "- 지금 문제의 함수(solution)나 변수 이름, 입력을 쓰지 않는다. 이 문제를 푸는 코드를 쓰지 않는다.")
TEMPLATE_TASK = ("[학생 질문] {q}\n"
                 "학생이 '{concept}'의 기본 틀을 원한다. 틀 코드는 앱이 따로 보여 주므로 너는 코드를 쓰지 않는다.\n"
                 "이 틀이 무엇을 하는지 한 문장, 지금 문제에 쓰기 전에 학생이 스스로 떠올려 볼 점을 질문 한 문장으로 쓴다.")
