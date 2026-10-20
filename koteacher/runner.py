"""harness.py를 별도 프로세스로 돌린다. 내 코드는 앱 프로세스 안에서 실행하지 않는다."""
import json
import subprocess
import sys
from pathlib import Path

from . import config

HARNESS = Path(__file__).with_name("harness.py")


def check(code: str, pid: str, repair=True, timeout=20):
    pack_path = config.PACKS / f"{pid}.json"
    req = json.dumps({"code": code, "pack": str(pack_path), "repair": repair})
    try:
        proc = subprocess.run(config.child_cmd("harness"), input=req, capture_output=True, timeout=timeout, cwd=str(config.DATA),
                              **config.child_kw())
    except subprocess.TimeoutExpired:
        return {"fatal": f"검사가 {timeout}초 안에 끝나지 않았습니다"}
    lines = [l for l in proc.stdout.splitlines() if l.startswith("{")]
    if not lines:
        return {"fatal": (proc.stderr or "검사 프로세스가 결과 없이 끝났습니다")[-800:]}
    return json.loads(lines[-1])
