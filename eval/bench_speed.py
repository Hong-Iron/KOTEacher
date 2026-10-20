"""코치 속도 실험. 같은 코치 호출(2군데 버그 3개)로 설정을 바꿔 가며 잰다.

    .venv/bin/python eval/bench_speed.py 기준
    .venv/bin/python eval/bench_speed.py 형식끔 문맥4k ...

재는 것 (각 버그마다, 미리 읽히기 뒤 실제 호출):
  첫 글자: 학생이 코치 말의 첫 글자를 보는 시간
  끝: 응답이 다 끝나는 시간 (말풍선 버튼이 뜨는 때)
  생성: 초당 생성 토큰, 처음 읽기: 캐시를 막았을 때 초당 프롬프트 토큰
"""
import json
import random
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koteacher import coach, config, ollama, runner  # noqa: E402

BUGS = ["pg42576", "pg17687", "pg258712"]


def one(variant):
    data = {b["pid"]: b for b in json.loads((ROOT / "eval/data/bugs2.json").read_text())}
    firsts, totals, gens, colds, lines = [], [], [], [], []
    for pid in BUGS:
        b = data[pid]
        code = b["code"] + f"\n# {random.random()}\n"
        r = runner.check(code, pid)
        fs = coach.facts(r)
        coach.warm(pid, code)  # 앱처럼: 문제를 열거나 타이핑이 멈출 때 미리 읽혀 둔다
        t0 = time.perf_counter()
        first = []
        d = coach.diagnose_and_say(pid, code, fs[0], r, on_message=lambda p: first or first.append(time.perf_counter() - t0))
        totals.append(time.perf_counter() - t0)
        firsts.append(first[0] if first else totals[-1])
        m = d.get("meta") or {}
        if m.get("eval_duration"):
            gens.append(m["eval_count"] / (m["eval_duration"] / 1e9))
        lines.append(d.get("line") in b["lines"])
        # 처음 읽기 속도: 맨 앞을 바꿔 캐시를 막는다
        msgs = coach.messages(pid, code, coach.evidence(fs[0], r), coach.DIAG_TASK)
        msgs[0]["content"] = f"[{random.random()}]\n" + msgs[0]["content"]
        _, m2 = ollama.chat(msgs, max_tokens=1)
        if m2.get("prompt_eval_duration"):
            colds.append(m2["prompt_eval_count"] / (m2["prompt_eval_duration"] / 1e9))
    print(f"{variant:<14} 첫 글자 {st.median(firsts):5.1f}초 · 끝 {st.median(totals):5.1f}초 · 생성 {st.median(gens) if gens else 0:4.1f} tok/s"
          f" · 처음 읽기 {st.median(colds) if colds else 0:4.0f} tok/s · 줄 적중 {sum(lines)}/{len(lines)} · 모델 {config.MODEL} 문맥 {config.NUM_CTX}",
          flush=True)


if __name__ == "__main__":
    ollama.status()
    ollama.load()
    for v in sys.argv[1:] or ["기준"]:
        one(v)
