"""사용자 코드를 문제 팩으로 검사하는 별도 프로세스.

    python -I harness.py  < {"code": ..., "pack": 경로, "repair": bool}

표준 출력 마지막 줄에 결과 JSON을 쓴다. 이 파일은 kotte 패키지를 import하지 않는다.
"""
import ast
import contextlib
import copy
import io
import json
import signal
import sys
import time
import traceback

PER_TEST = 2.0        # 테스트 하나의 시간 제한(초)
HIDDEN_BUDGET = 3.0   # 숨은 검사 전체 시간
REPAIR_BUDGET = 1.5   # 수리 검색 전체 시간
REPAIR_PER_TEST = 0.2
MAX_OUT = 4000


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


signal.signal(signal.SIGALRM, _alarm)


def norm(x):
    """튜플과 리스트를 같게 본다 (프로그래머스 채점과 같게)."""
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    if isinstance(x, float):
        return round(x, 9)
    return x


def call(fn, args, limit):
    signal.setitimer(signal.ITIMER_REAL, limit)
    t = time.perf_counter()
    try:
        out = fn(*copy.deepcopy(args))
        return {"out": out, "ms": (time.perf_counter() - t) * 1000}
    except Timeout:
        return {"timeout": True, "ms": limit * 1000}
    except RecursionError:
        return {"error": "RecursionError: 재귀가 너무 깊다", "line": None, "ms": (time.perf_counter() - t) * 1000}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        line = next((f.lineno for f in reversed(tb) if f.filename == "<내 코드>"), None)
        return {"error": f"{type(e).__name__}: {e}", "line": line, "ms": (time.perf_counter() - t) * 1000}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


def load_solution(code_or_tree):
    g = {"__name__": "user"}
    exec(compile(code_or_tree, "<내 코드>", "exec"), g)
    fn = g.get("solution")
    if not callable(fn):
        raise NameError("solution 함수가 없다")
    return fn


def short(s, n=300):
    return s if len(s) <= n else s[:n] + "…"


def run_tests(fn, tests, limit, budget=None, stop_after=None):
    """tests: [(args, expected_repr, expected)] → 결과 목록. 실패가 stop_after개면 멈춘다."""
    res, fails, start = [], 0, time.perf_counter()
    for args, exp_repr, exp in tests:
        if budget and time.perf_counter() - start > budget:
            break
        r = call(fn, args, limit)
        ok = "out" in r and norm(r["out"]) == norm(exp)
        r["ok"] = ok
        res.append(r)
        if r.get("timeout"):  # 무한 루프면 남은 검사도 오래 걸린다. 여기서 멈춘다
            break
        if not ok:
            fails += 1
            if stop_after and fails >= stop_after:
                break
    return res


# ---------- 수리 검색: 한 군데만 고쳐서 모든 검사가 통과하는지 ----------
SWAP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
        ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
OPSYM = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!="}


def mutation_sites(tree):
    """(노드 번호, 종류, 설명) 목록. 노드 번호는 ast.walk 순서."""
    sites = []
    nodes = list(ast.walk(tree))
    parents = {}
    for p in nodes:
        for c in ast.iter_child_nodes(p):
            parents[id(c)] = p
    for i, n in enumerate(nodes):
        line = getattr(n, "lineno", None)
        if isinstance(n, ast.Compare):
            for k, op in enumerate(n.ops):
                if type(op) in SWAP:
                    sites.append((i, ("cmp", k), line, f"{OPSYM[type(op)]} → {OPSYM[SWAP[type(op)]]}", "비교·경계"))
        elif isinstance(n, ast.Constant) and type(n.value) is int and not isinstance(parents.get(id(n)), ast.Subscript):
            for d in (1, -1):
                sites.append((i, ("const", d), line, f"{n.value} → {n.value + d}", "비교·경계"))
        elif isinstance(n, ast.BoolOp):
            sites.append((i, ("bool",), line, "and ↔ or", "조건 놓침"))
        elif isinstance(n, ast.BinOp) and type(n.op) in (ast.Add, ast.Sub):
            sites.append((i, ("addsub",), line, "+ ↔ -", "기타"))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("min", "max"):
            sites.append((i, ("minmax",), line, f"{n.func.id} → {'max' if n.func.id == 'min' else 'min'}", "기타"))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "range":
            for k, a in enumerate(n.args):
                if not isinstance(a, ast.Constant):
                    for d in (1, -1):
                        sites.append((i, ("rangearg", k, d), line, f"range의 {k + 1}번째 값 {'+1' if d > 0 else '-1'}", "인덱스"))
        if isinstance(n, ast.Subscript) and not isinstance(n.slice, (ast.Slice, ast.Constant, ast.Tuple)):
            for d in (1, -1):
                sites.append((i, ("index", d), line, f"인덱스 {'+1' if d > 0 else '-1'}", "인덱스"))
    return sites


def apply_mutation(code, site):
    tree = ast.parse(code)
    nodes = list(ast.walk(tree))
    i, kind = site[0], site[1]
    n = nodes[i]
    if kind[0] == "cmp":
        n.ops[kind[1]] = SWAP[type(n.ops[kind[1]])]()
    elif kind[0] == "const":
        n.value += kind[1]
    elif kind[0] == "bool":
        n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
    elif kind[0] == "addsub":
        n.op = ast.Sub() if isinstance(n.op, ast.Add) else ast.Add()
    elif kind[0] == "minmax":
        n.func.id = "max" if n.func.id == "min" else "min"
    elif kind[0] == "rangearg":
        _, k, d = kind
        n.args[k] = ast.BinOp(n.args[k], ast.Add() if d > 0 else ast.Sub(), ast.Constant(1))
    elif kind[0] == "index":
        n.slice = ast.BinOp(n.slice, ast.Add() if kind[1] > 0 else ast.Sub(), ast.Constant(1))
    ast.fix_missing_locations(tree)
    return tree


def repair(code, failing, all_tests):
    sites = mutation_sites(ast.parse(code))
    lines = code.splitlines()
    start, fixes, tried = time.perf_counter(), [], 0
    for site in sites:
        if time.perf_counter() - start > REPAIR_BUDGET or tried >= 400:
            break
        tried += 1
        try:
            tree = apply_mutation(code, site)
            with contextlib.redirect_stdout(io.StringIO()):
                fn = load_solution(tree)
                if not all(r["ok"] for r in run_tests(fn, failing, REPAIR_PER_TEST, stop_after=1)):
                    continue
                if all(r["ok"] for r in run_tests(fn, all_tests, REPAIR_PER_TEST, budget=0.6, stop_after=1)):
                    new_line = ast.unparse(tree).splitlines()  # 참고용
                    fixes.append({"line": site[2], "label": site[3], "category": site[4],
                                  "before": lines[site[2] - 1].strip() if site[2] else ""})
        except Exception:
            continue
        if len(fixes) >= 3:
            break
    return {"tried": tried, "sites": len(sites), "fixes": fixes, "ms": (time.perf_counter() - start) * 1000}


def main():
    req = json.loads(sys.stdin.read())
    code, pack = req["code"], json.load(open(req["pack"], encoding="utf-8"))
    out = {"syntax": None, "load_error": None, "examples": [], "hidden": None, "repair": None, "stdout": ""}
    try:
        ast.parse(code)
    except SyntaxError as e:
        out["syntax"] = {"line": e.lineno, "col": e.offset, "msg": e.msg}
        print(json.dumps(out, ensure_ascii=False))
        return
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            fn = load_solution(code)
    except Exception as e:
        out["load_error"] = f"{type(e).__name__}: {e}"
        print(json.dumps(out, ensure_ascii=False))
        return

    lit = ast.literal_eval
    ex_tests = [(lit(a), o, lit(o)) for a, o in pack["examples"]]
    hid_tests = [(lit(a), o, lit(o)) for a, o in pack["hidden"]]

    with contextlib.redirect_stdout(buf):
        ex_res = run_tests(fn, ex_tests, PER_TEST)
    for (args, exp_repr, _), r in zip(ex_tests, ex_res):
        item = {"args": short(repr(args)[1:-1].rstrip(",")), "expected": short(exp_repr), "ok": r["ok"], "ms": round(r["ms"], 2)}
        if "out" in r:
            item["got"] = short(repr(r["out"]))
        for k in ("error", "line", "timeout"):
            if k in r:
                item[k] = r[k]
        out["examples"].append(item)
    for args, exp_repr, _ in ex_tests[len(ex_res):]:
        out["examples"].append({"args": short(repr(args)[1:-1].rstrip(",")), "expected": short(exp_repr), "ok": False, "skipped": True, "ms": 0})

    hid = {"total": len(hid_tests), "run": 0, "passed": 0, "first_fail": None}
    timed_out = any(r.get("timeout") for r in ex_res)
    with contextlib.redirect_stdout(buf):
        hres = [] if timed_out else run_tests(fn, hid_tests, PER_TEST, budget=HIDDEN_BUDGET, stop_after=1)
    hid["run"] = len(hres)
    hid["passed"] = sum(r["ok"] for r in hres)
    if hres and not hres[-1]["ok"]:
        args, exp_repr, _ = hid_tests[len(hres) - 1]
        r = hres[-1]
        ff = {"args": short(repr(args)[1:-1].rstrip(","), 600), "expected": short(exp_repr), "index": len(hres) - 1}
        if "out" in r:
            ff["got"] = short(repr(r["out"]))
        for k in ("error", "line", "timeout"):
            if k in r:
                ff[k] = r[k]
        hid["first_fail"] = ff
    out["hidden"] = hid
    out["stdout"] = buf.getvalue()[:MAX_OUT]

    failing = [t for t, r in zip(ex_tests, ex_res) if not r["ok"]]
    if hid["first_fail"]:
        failing.append(hid_tests[hid["first_fail"]["index"]])
    if req.get("repair") and failing and not any(r.get("timeout") for r in ex_res + hres):
        out["repair"] = repair(code, failing[:3], ex_tests + hid_tests[:120])
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    sys.setrecursionlimit(10 ** 6)
    main()
