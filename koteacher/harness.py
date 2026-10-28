"""사용자 코드를 문제 팩으로 검사하는 별도 프로세스.

    python -I harness.py  < {"code": ..., "pack": 경로, "repair": bool, "only": None | "examples" | "submit"}

only="examples"는 예시만 돌린다 (실전 모드의 예시 실행). only="submit"은 히든 테스트를 실패해도 끝까지 돌리고
통과 개수만 낸다 (실전 모드의 제출: 반례·수리·실행 추적 없음).

표준 출력 마지막 줄에 결과 JSON을 쓴다. 이 파일은 koteacher 패키지를 import하지 않는다.
"""
import ast
import contextlib
import copy
import io
import json
import threading
import _thread
import sys
import time
import traceback

PER_TEST = 2.0        # 테스트 하나의 시간 제한(초)
HIDDEN_BUDGET = 3.0   # 히든 테스트 전체 시간
SUBMIT_BUDGET = 12.0  # 실전 제출에서 히든 테스트 전체 시간
REPAIR_BUDGET = 1.5   # 변이 탐색 전체 시간
REPAIR_PER_TEST = 0.2
LOAD_LIMIT = 2.0      # 함수 밖 코드(맨 아래에서 직접 부른 함수 등)를 실행하는 시간 제한(초)
MAX_OUT = 4000


class Deadline:
    """시간 제한. 맥·리눅스·윈도에서 똑같이 돈다: 다른 스레드가 정해진 시간 뒤 주 스레드에
    KeyboardInterrupt를 넣는다. 학생 코드의 `except Exception:`에 잡히지 않는 예외다."""

    def __init__(self, sec):
        self.sec, self.lock, self.active, self.fired = sec, threading.Lock(), False, False

    def _fire(self):
        with self.lock:
            if self.active:
                self.fired = True
                _thread.interrupt_main()

    def __enter__(self):
        self.active = True
        self.timer = threading.Timer(self.sec, self._fire)
        self.timer.daemon = True
        self.timer.start()
        return self

    def __exit__(self, *exc):
        with self.lock:
            self.active = False
        self.timer.cancel()
        return False


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
    t = time.perf_counter()
    dl = Deadline(limit)
    try:
        with dl:
            out = fn(*copy.deepcopy(args))
        return {"out": out, "ms": (time.perf_counter() - t) * 1000}
    except KeyboardInterrupt:
        return {"timeout": True, "ms": limit * 1000}
    except RecursionError:
        return {"error": "RecursionError: 재귀가 너무 깊습니다", "line": None, "ms": (time.perf_counter() - t) * 1000}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        line = next((f.lineno for f in reversed(tb) if f.filename == "<내 코드>"), None)
        return {"error": f"{type(e).__name__}: {e}", "line": line, "ms": (time.perf_counter() - t) * 1000}


def load_solution(code_or_tree):
    g = {"__name__": "user"}
    exec(compile(code_or_tree, "<내 코드>", "exec"), g)
    fn = g.get("solution")
    if not callable(fn):
        raise NameError("solution 함수가 없습니다")
    return fn


class LoadTimeout(Exception):
    """함수 밖 코드가 제한 시간 안에 끝나지 않았다. line은 멈춘 줄, called는 그 코드를 부른 맨 바깥 줄."""

    def __init__(self, line, called):
        super().__init__(line)
        self.line, self.called = line, called


def load_limited(code_or_tree, limit):
    """load_solution에 시간 제한을 건다. 코드를 불러올 때는 함수 밖 코드도 실행되므로, 맨 아래에서 부른
    함수가 끝나지 않으면(무한 반복 등) 불러오기가 끝나지 않는다. 예전에는 제한이 없어 검사 전체가 20초에 끊겼다."""
    try:
        with Deadline(limit):
            return load_solution(code_or_tree)
    except KeyboardInterrupt as e:
        tb = [f for f in traceback.extract_tb(e.__traceback__) if f.filename == "<내 코드>"]
        raise LoadTimeout(tb[-1].lineno if tb else None, tb[0].lineno if tb else None) from None


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


# ---------- 변이 탐색: 한 군데만 고쳐서 모든 검사가 통과하는지 ----------
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


def repair(code, failing, all_tests, load_limit=REPAIR_PER_TEST):
    """load_limit: 바꿔 본 코드 하나를 불러오는 시간 제한. 바꾼 곳이 맨 아래에서 부른 함수 안이면
    (예: while num > 0 → while num >= 0) 불러오기가 끝나지 않으므로, 내 코드를 불러온 시간에 맞춘 제한을 건다."""
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
                fn = load_limited(tree, load_limit)  # 끝나지 않으면 LoadTimeout → 다음 후보로
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


def trace_run(code, args, max_rows=40):
    """가장 작은 반례에서 줄마다 바뀐 지역 변수를 기록한다 (AI 진단 재료)."""
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            fn = load_limited(code, LOAD_LIMIT)
    except LoadTimeout:
        return []
    rows, state = [], {}  # 프레임마다 (직전 변수, 직전 줄)

    def short_val(v):
        r = repr(v)
        return r if len(r) <= 40 else r[:37] + "…"

    def tr(frame, event, arg):
        if frame.f_code.co_filename != "<내 코드>":
            return None
        if len(rows) >= max_rows:
            return None
        key = id(frame)
        if event == "call":
            state[key] = ({k: short_val(v) for k, v in frame.f_locals.items()}, None)
            return tr
        if event not in ("line", "return"):
            return tr
        prev, last = state.get(key, ({}, None))
        cur = {k: short_val(v) for k, v in frame.f_locals.items() if not k.startswith("__") and not callable(v)}
        changed = {k: v for k, v in cur.items() if prev.get(k) != v}
        done_line = frame.f_lineno if event == "return" else last  # 줄 이벤트는 그 줄을 실행하기 직전에 온다
        if done_line and (changed or event == "return"):
            row = {"line": done_line, "fn": frame.f_code.co_name, "vars": changed}
            if event == "return":
                row["ret"] = short_val(arg)
            rows.append(row)
        state[key] = (cur, frame.f_lineno)
        return tr

    sys.settrace(tr)
    try:
        with Deadline(0.5), contextlib.redirect_stdout(io.StringIO()):
            fn(*copy.deepcopy(args))
    except BaseException:
        pass
    finally:
        sys.settrace(None)
    return rows


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
    t_load = time.perf_counter()
    try:
        with contextlib.redirect_stdout(buf):
            fn = load_limited(code, LOAD_LIMIT)
    except LoadTimeout as e:
        # 멈춘 줄(line)에 표시하고, 함수 밖에서 그 함수를 부른 줄(called)을 말해 준다. 그때까지 print한 것은 출력에 남긴다
        where = f"{e.called}번 줄에서 부른 코드가" if e.called and e.called != e.line else "함수 밖 코드가"
        out.update(load_error=f"시간 초과: {where} {LOAD_LIMIT:g}초 안에 끝나지 않았습니다", load_line=e.line,
                   load_timeout=True, stdout=buf.getvalue()[:MAX_OUT])
        print(json.dumps(out, ensure_ascii=False))
        return
    except Exception as e:
        out["load_error"] = f"{type(e).__name__}: {e}"
        # 함수 밖 코드에서 난 오류(예: 맨 줄에 쓴 글자 → NameError)의 줄 번호
        tb = traceback.extract_tb(e.__traceback__)
        out["load_line"] = next((f.lineno for f in reversed(tb) if f.filename == "<내 코드>"), None)
        out["stdout"] = buf.getvalue()[:MAX_OUT]  # 오류가 나기 전까지 print한 것
        print(json.dumps(out, ensure_ascii=False))
        return
    t_load = time.perf_counter() - t_load

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

    only = req.get("only")
    if only == "examples":
        out["stdout"] = buf.getvalue()[:MAX_OUT]
        print(json.dumps(out, ensure_ascii=False))
        return
    if only == "submit":
        # 실전 제출: 틀려도 멈추지 않고 끝까지 돌려 개수만 센다. 검사는 작은 입력부터라서
        # 시간 초과가 두 번 나면 남은(더 큰) 검사도 넘을 것으로 보고 멈춘다
        sub = {"total": len(hid_tests), "passed": 0, "wrong": 0, "timeout": 0, "error": 0, "not_run": 0, "stopped": None}
        start = time.perf_counter()
        with contextlib.redirect_stdout(buf):
            for i, (args, _, exp) in enumerate(hid_tests):
                if sub["timeout"] >= 2 or time.perf_counter() - start > SUBMIT_BUDGET:
                    sub["not_run"] = len(hid_tests) - i
                    sub["stopped"] = "timeout" if sub["timeout"] >= 2 else "budget"
                    break
                r = call(fn, args, PER_TEST)
                if r.get("timeout"):
                    sub["timeout"] += 1
                elif "error" in r:
                    sub["error"] += 1
                elif norm(r["out"]) == norm(exp):
                    sub["passed"] += 1
                else:
                    sub["wrong"] += 1
        sub["sec"] = round(time.perf_counter() - start, 2)
        out["submit"] = sub
        out["stdout"] = buf.getvalue()[:MAX_OUT]
        print(json.dumps(out, ensure_ascii=False))
        return

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
    if req.get("repair") and failing:
        smallest = min(failing, key=lambda t: len(repr(t[0])))
        if len(repr(smallest[0])) <= 300:
            out["trace"] = trace_run(code, smallest[0])
            out["trace_args"] = short(repr(smallest[0])[1:-1].rstrip(","), 300)
        # 시간 초과가 난 경우에도 돌린다. 변이체의 테스트마다 짧은 제한(REPAIR_PER_TEST)이 걸려 있다
        slow = any(r.get("timeout") for r in ex_res + hres)
        # 바꿔 본 코드를 불러오는 제한: 내 코드를 불러온 시간의 3배 (적어도 REPAIR_PER_TEST, 많아야 LOAD_LIMIT)
        load_limit = min(LOAD_LIMIT, max(REPAIR_PER_TEST, 3 * t_load))
        out["repair"] = repair(code, failing[:2 if slow else 3], ex_tests + hid_tests[:120], load_limit)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    sys.setrecursionlimit(10 ** 6)
    main()
