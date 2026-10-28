"""harness.py를 별도 프로세스로 돌린다. 내 코드는 앱 프로세스 안에서 실행하지 않는다."""
import json
import subprocess
import sys
import threading
from pathlib import Path

from . import config

HARNESS = Path(__file__).with_name("harness.py")
_auto = set()  # 끊어도 되는 검사(자동 검사) 프로세스. 자동 검사 중에 실행을 누르면 cancel()이 끊는다
_lock = threading.Lock()


def check(code: str, pid: str, repair=True, timeout=20, only=None, cancellable=False):
    """돌려주는 값: harness의 결과, 또는 {"fatal": 이유}, 끊었으면 {"cancelled": True}.
    timeout은 안전망이다: 함수 밖 코드·테스트·변이 탐색에는 harness가 따로 시간 제한을 건다."""
    pack_path = config.PACKS / f"{pid}.json"
    req = json.dumps({"code": code, "pack": str(pack_path), "repair": repair and not only, "only": only})
    proc = subprocess.Popen(config.child_cmd("harness"), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=str(config.DATA), **config.child_kw())
    proc.cancelled = False
    if cancellable:
        with _lock:
            _auto.add(proc)
    try:
        stdout, stderr = proc.communicate(req, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return {"fatal": f"검사가 {timeout}초 안에 끝나지 않았습니다"}
    finally:
        with _lock:
            _auto.discard(proc)
    if proc.cancelled:
        return {"cancelled": True}
    lines = [l for l in stdout.splitlines() if l.startswith("{")]
    if not lines:
        return {"fatal": (stderr or "검사 프로세스가 결과 없이 끝났습니다")[-800:]}
    return json.loads(lines[-1])


def cancel():
    """도는 중인 자동 검사를 끊는다. 하나라도 끊었으면 True."""
    with _lock:
        procs = [p for p in _auto if p.poll() is None]
    for p in procs:
        p.cancelled = True
        p.kill()
    return bool(procs)
