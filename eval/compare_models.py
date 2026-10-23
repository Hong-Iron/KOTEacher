"""코치 모델 견주기. 같은 평가를 모델마다 돌리고 한 표로 모은다.

    .venv/bin/python eval/compare_models.py gemma4:e4b-it-qat qwen3.5:4b qwen3.5:9b exaone3.5:7.8b

모델마다 별도 프로세스에서 (KOTEACHER_MODEL로 모델을 고정하고, 외부 API 설정은 무시)
  1. 2군데 버그 12개 (eval/data/_sub, e4b·12B를 견줄 때 쓴 것과 같은 묶음): 줄 적중, 시간, 코치 말
  2. 1군데 버그 10개 말하기: 고칠 값을 흘리는지
를 재고, 코치 말에서 한국어 품질(한자·가나 섞임, 영어 낱말 비율, 질문으로 끝나는지)을 센다.
결과: eval/results/cmp_<모델>_{llm,say}.json, 표는 표준 출력과 eval/results/compare.md
평가 중에는 KOTEacher 앱을 꺼 둔다 (앱이 다른 모델을 붙잡고 있으면 메모리가 모자란다).
"""
import json
import os
import re
import statistics as st
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "eval/results"


def slug(m):
    return re.sub(r"[^a-z0-9]+", "_", m.lower()).strip("_")


def unload(m):
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=json.dumps({"model": m, "keep_alive": 0}).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=30).read()
    except Exception:
        pass


def one(model):
    """이 프로세스는 모델 하나만 잰다."""
    sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "eval"))
    from koteacher import ollama
    import run_eval
    st_ = ollama.status()
    if not st_["model"] or st_["name"] != model:
        sys.exit(f"{model}이 없습니다: {st_}")
    ollama.load()  # 불러오는 시간은 빼고 잰다
    run_eval.DATA = ROOT / "eval/data/_sub"
    run_eval.llm(12, f"cmp_{slug(model)}_llm")
    run_eval.DATA = ROOT / "eval/data"
    run_eval.say_eval(10, f"cmp_{slug(model)}_say")


HANJA = re.compile(r"[一-鿿぀-ヿ]")       # 한자·가나
ENG = re.compile(r"(?<![A-Za-z_\[\.])[A-Za-z]{4,}(?![A-Za-z_\(\[])")  # 코드 이름처럼 붙은 것은 뺀 영어 낱말


def korean(rows):
    msgs = [r["message"] for r in rows if r.get("source") == "ai"]
    if not msgs:
        return {"ai": 0}
    words = lambda m: max(1, len(m.split()))
    return {"ai": len(msgs),
            "hanja": sum(bool(HANJA.search(m)) for m in msgs),
            "eng": round(st.mean(len(ENG.findall(m)) / words(m) for m in msgs), 3),
            "q": sum(m.rstrip().endswith("?") for m in msgs),
            "len": int(st.median(len(m) for m in msgs))}


def table(models):
    out = ["| 모델 | 줄 적중 (12) | 응답 끝 중앙값 | 첫 글자 | 유출 (22) | 질문으로 끝남 | 한자·가나 섞임 | 영어 낱말 비율 | 말 길이 |",
           "|---|---|---|---|---|---|---|---|---|"]
    for m in models:
        try:
            a = json.loads((RES / f"cmp_{slug(m)}_llm.json").read_text())
            b = json.loads((RES / f"cmp_{slug(m)}_say.json").read_text())
        except FileNotFoundError:
            out.append(f"| {m} | (결과 없음) |"); continue
        rows = a + b
        k = korean(rows)
        fm = [r["first_msg_char"] for r in a if r.get("first_msg_char")]
        out.append(f"| {m} | {sum(r['diag_line_ok'] for r in a)}/{len(a)} | {st.median(r['total'] for r in a):.1f}초 | "
                   f"{st.median(fm) if fm else 0:.1f}초 | {sum(bool(r['leak']) for r in rows)} | "
                   f"{k.get('q', 0)}/{k['ai']} | {k.get('hanja', 0)}/{k['ai']} | {k.get('eng', 0):.0%} | {k.get('len', 0)}자 |")
    return "\n".join(out)


if __name__ == "__main__":
    if sys.argv[1] == "--one":
        one(sys.argv[2])
        sys.exit()
    if sys.argv[1] == "--table":
        print(table(sys.argv[2:]))
        sys.exit()
    models = sys.argv[1:]
    env = dict(os.environ, KOTEACHER_PROVIDER="ollama")
    for m in models:
        print(f"\n===== {m}", flush=True)
        subprocess.run([sys.executable, __file__, "--one", m], env=dict(env, KOTEACHER_MODEL=m))
        unload(m)
    t = table(models)
    print("\n" + t)
    (RES / "compare.md").write_text(t + "\n", encoding="utf-8")
