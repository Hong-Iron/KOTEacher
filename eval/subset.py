"""지난 결과에서 고른 버그만 다시 돌린다: python eval/subset.py <이전 결과 이름> <새 이름>"""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "eval"))
import run_eval
prev = json.loads((ROOT / "eval/results" / f"{sys.argv[1]}.json").read_text())
bad = [r["pid"] for r in prev if not r["diag_line_ok"]]
good = [r["pid"] for r in prev if r["diag_line_ok"]][:5]
want = set(bad + good)
bugs = [b for b in json.loads((ROOT / "eval/data/bugs2.json").read_text()) if b["pid"] in want]
(ROOT / "eval/data/_subset.json").write_text(json.dumps(bugs, ensure_ascii=False))
orig = run_eval.DATA / "bugs2.json"
run_eval.DATA = ROOT / "eval/data/_sub"; run_eval.DATA.mkdir(exist_ok=True)
(run_eval.DATA / "bugs2.json").write_text(json.dumps(bugs, ensure_ascii=False))
print("이전에 틀린 것:", bad)
run_eval.llm(len(bugs), sys.argv[2])
