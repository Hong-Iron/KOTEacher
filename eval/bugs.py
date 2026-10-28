"""모범 풀이에 버그를 심어 '학생 코드' 시험지를 만든다.

- 모범 풀이: 볼트 코드 파일에서 solution과 그것이 부르는 함수, import, 상수만 남긴 것
- 1군데 버그: 변이 탐색이 잡아야 하는 것
- 2군데 버그: 한 군데 수정으로는 못 고친다 → AI 진단으로 간다
버그를 심은 코드가 실제로 검사에서 떨어지는 것만 쓴다.
"""
import ast
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "koteacher"))
from koteacher import config, runner, packs  # noqa: E402
import harness  # noqa: E402  (mutation_sites, apply_mutation)

OUT = ROOT / "eval" / "data"


def student_code(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    body = [n for n in tree.body if not (isinstance(n, ast.If) and "__main__" in ast.unparse(n.test))]
    funcs = {n.name: n for n in body if isinstance(n, ast.FunctionDef)}
    keep, todo = set(), ["solution"]
    while todo:
        f = todo.pop()
        if f in keep or f not in funcs:
            continue
        keep.add(f)
        todo += [n.id for n in ast.walk(funcs[f]) if isinstance(n, ast.Name) and n.id in funcs]
    out = [n for n in body if not isinstance(n, ast.FunctionDef) or n.name in keep]
    # 문서 문자열(모듈 설명)은 뺀다
    out = [n for n in out if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
    return ast.unparse(ast.Module(out, [])) + "\n"


def solution_lines(code):
    tree = ast.parse(code)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "solution")
    return fn.lineno, fn.end_lineno


def make(seed=0, per_problem=3):
    rng = random.Random(seed)
    one, two = [], []
    for f in packs.code_files():
        pid = packs.pid_of(f)
        code = student_code(f)
        base = runner.check(code, pid, repair=False)
        if not all(e["ok"] for e in base.get("examples", [])) or (base.get("hidden") or {}).get("first_fail"):
            print("모범 풀이가 자기 팩을 통과하지 못함:", pid)
            continue
        lo, hi = solution_lines(code)
        sites = [s for s in harness.mutation_sites(ast.parse(code)) if s[2] and lo < s[2] <= hi]
        rng.shuffle(sites)
        got1 = 0
        for s in sites:
            if got1 >= per_problem:
                break
            try:
                mcode = ast.unparse(harness.apply_mutation(code, s)) + "\n"
            except Exception:
                continue
            r = runner.check(mcode, pid, repair=False)
            if r.get("syntax") or r.get("fatal"):
                continue
            failed = not all(e["ok"] for e in r.get("examples", [])) or (r.get("hidden") or {}).get("first_fail")
            if failed:
                one.append({"pid": pid, "code": mcode, "lines": [s[2]], "labels": [s[3]], "categories": [s[4]]})
                got1 += 1
        # 2군데: 서로 다른 줄 두 곳
        got2, tries = 0, 0
        while got2 < 1 and tries < 30 and len(sites) >= 2:
            tries += 1
            a, b = rng.sample(sites, 2)
            if a[2] == b[2]:
                continue
            try:
                m1 = ast.unparse(harness.apply_mutation(code, a)) + "\n"
                # 첫 변이 뒤 줄 번호가 그대로인지 확인하고 두 번째 변이를 같은 자리에 건다
                sites2 = [s for s in harness.mutation_sites(ast.parse(m1)) if s[2] == b[2] and s[3] == b[3]]
                if not sites2:
                    continue
                m2 = ast.unparse(harness.apply_mutation(m1, sites2[0])) + "\n"
            except Exception:
                continue
            r = runner.check(m2, pid, repair=True)
            if r.get("syntax") or r.get("fatal") or any(e.get("timeout") for e in r.get("examples", [])):
                continue
            failed = not all(e["ok"] for e in r.get("examples", [])) or (r.get("hidden") or {}).get("first_fail")
            if failed and not (r.get("repair") or {}).get("fixes"):
                two.append({"pid": pid, "code": m2, "lines": [a[2], b[2]], "labels": [a[3], b[3]], "categories": [a[4], b[4]]})
                got2 += 1
        print(pid, "1군데", got1, "2군데", got2, flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "bugs1.json").write_text(json.dumps(one, ensure_ascii=False, indent=0), encoding="utf-8")
    (OUT / "bugs2.json").write_text(json.dumps(two, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"1군데 {len(one)}개, 2군데 {len(two)}개")


if __name__ == "__main__":
    make()
