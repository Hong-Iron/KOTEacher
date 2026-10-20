"""볼트 풀이 코드의 검사 블록을 실행하면서 solution 호출(입력, 기준 답)을 기록한다.

별도 프로세스에서 `python -I capture.py <코드 파일>`로 실행하고, 결과 JSON을 표준 출력 마지막 줄에 쓴다.
- 예시: 처음으로 random.Random(또는 random.seed)이 불리기 전의 호출
- 숨은 검사: 그 뒤의 호출
- solution의 필수 인자 수와 같은 호출만 기록한다 (추적용 인자를 더 받는 호출은 뺀다)
- 재귀 호출은 바깥 호출만 기록한다
"""
import ast
import contextlib
import copy
import inspect
import io
import json
import random
import sys

MAX_REPR = 20000


def main(path):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    main_nodes = [n for n in tree.body if isinstance(n, ast.If) and "__main__" in ast.unparse(n.test)]
    pre = ast.Module([n for n in tree.body if n not in main_nodes], [])
    g = {"__name__": "ref", "__file__": path}
    exec(compile(pre, path, "exec"), g)
    orig = g["solution"]
    params = list(inspect.signature(orig).parameters.values())
    required = [p.name for p in params if p.default is inspect.Parameter.empty
                and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]

    # 검사 블록에 리터럴로 적힌 값들. 예시는 인자가 모두 여기 들어 있는 호출이다.
    literals = set()
    for node in main_nodes:
        for sub in ast.walk(node):
            if isinstance(sub, (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set, ast.UnaryOp)):
                try:
                    literals.add(repr(ast.literal_eval(sub)))
                except Exception:
                    pass

    state = {"phase": "example", "depth": 0}
    examples, hidden, seen, early = [], [], set(), []

    real_init = random.Random.__init__
    real_seed = random.seed

    def init(self, *a, **k):
        state["phase"] = "hidden"
        real_init(self, *a, **k)

    def seed(*a, **k):
        state["phase"] = "hidden"
        real_seed(*a, **k)

    random.Random.__init__ = init
    random.seed = seed

    def wrapper(*args, **kwargs):
        # 추적용 인자를 더 받는 호출은 필수 인자만 떼어 기록한다 (답은 같다)
        record = state["depth"] == 0 and not kwargs and len(args) >= len(required)
        before = copy.deepcopy(args[:len(required)]) if record else None
        state["depth"] += 1
        try:
            out = orig(*args, **kwargs)
        finally:
            state["depth"] -= 1
        if record:
            a, o = repr(before), repr(out)
            key = a
            if len(a) <= MAX_REPR and len(o) <= MAX_REPR and key not in seen:
                try:
                    ast.literal_eval(a), ast.literal_eval(o)
                except Exception:
                    return out
                seen.add(key)
                official = state["phase"] == "example" and len(examples) < 8 and all(repr(x) in literals for x in before)
                (examples if official else hidden).append([a, o])
                if not official and state["phase"] == "example":
                    early.append([a, o])
        return out

    g["solution"] = wrapper
    g["__name__"] = "__main__"
    buf = io.StringIO()
    ok, err = True, ""
    try:
        with contextlib.redirect_stdout(buf):
            for node in main_nodes:
                exec(compile(ast.Module(node.body, []), path, "exec"), g)
    except Exception as e:  # 기록은 남기고 실패를 알린다
        ok, err = False, f"{type(e).__name__}: {e}"
    if not examples and early:  # 리터럴 예시가 없으면 무작위 검사 전 첫 호출 3개를 예시로
        examples = early[:3]
        hidden = [h for h in hidden if h not in examples]
    print(json.dumps({
        "ok": ok and "ALL CHECKS PASSED" in buf.getvalue(), "error": err,
        "params": required, "examples": examples, "hidden": hidden,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
