"""문제 팩: 볼트 풀이 코드에서 기록한 예시와 숨은 검사.

팩은 볼트에서 언제든 다시 만들 수 있으므로 앱 데이터 폴더에 둔다.
"""
import ast
import json
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import config

CAPTURE = Path(__file__).with_name("capture.py")
HIDDEN_SMALL = 300   # 작은 입력부터 이만큼
HIDDEN_EXTRA = 40    # 나머지에서 무작위로 이만큼 (큰 입력 섞기)


def code_files():
    return sorted(config.PRACTICE.glob("*_pg*_p1.py"))


def pid_of(path: Path) -> str:
    return path.name.split("_")[1]  # 18_pg67258_p1.py → pg67258


def _select_hidden(hidden):
    hidden = sorted(hidden, key=lambda t: (len(t[0]), t[0]))
    small, rest = hidden[:HIDDEN_SMALL], hidden[HIDDEN_SMALL:]
    rng = random.Random(0)
    extra = rng.sample(rest, min(HIDDEN_EXTRA, len(rest)))
    return small + sorted(extra, key=lambda t: len(t[0]))


def build_one(path: Path, timeout=300):
    proc = subprocess.run(config.child_cmd("capture", str(path)),
                          capture_output=True, timeout=timeout, cwd=path.parent, **config.child_kw())
    lines = [l for l in proc.stdout.splitlines() if l.startswith("{")]
    if not lines:
        return {"id": pid_of(path), "file": path.name, "ok": False, "error": proc.stderr[-500:]}
    res = json.loads(lines[-1])
    pack = {
        "id": pid_of(path), "file": path.name, "ok": res["ok"], "error": res["error"],
        "params": res["params"], "examples": res["examples"],
        "hidden": _select_hidden(res["hidden"]), "hidden_total": len(res["hidden"]),
    }
    config.ensure_dirs()
    (config.PACKS / f"{pack['id']}.json").write_text(json.dumps(pack, ensure_ascii=False), encoding="utf-8")
    return pack


def build_all(workers=4):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(build_one, code_files()))


def load(pid: str):
    p = config.PACKS / f"{pid}.json"
    if not p.exists():
        src = next((f for f in code_files() if pid_of(f) == pid), None)
        if src is None:
            raise KeyError(pid)
        return build_one(src)
    return json.loads(p.read_text(encoding="utf-8"))


def literal(s):
    return ast.literal_eval(s)
