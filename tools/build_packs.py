"""볼트의 풀이 코드 90개로 문제 팩을 만든다.

    .venv/bin/python tools/build_packs.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from koteacher import packs  # noqa: E402

t = time.time()
res = packs.build_all()
bad = [p for p in res if not p["ok"]]
no_ex = [p["id"] for p in res if p.get("ok") and not p["examples"]]
no_hid = [p["id"] for p in res if p.get("ok") and not p["hidden"]]
print(f"팩 {len(res)}개, {time.time() - t:.0f}초")
print(f"예시 합계 {sum(len(p.get('examples', [])) for p in res)}, 숨은 검사 합계 {sum(len(p.get('hidden', [])) for p in res)}")
print("실패:", [(p["id"], p.get("error", "")[:120]) for p in bad])
print("예시 없음:", no_ex)
print("숨은 검사 없음:", no_hid)
