"""코치 평가.

    .venv/bin/python eval/run_eval.py det            # 1군데 버그: 결정적 단계(규칙·수리)만
    .venv/bin/python eval/run_eval.py llm [N] [tag]  # 2군데 버그: AI 진단 + 말하기, 앞에서 N개
결과는 eval/results/<이름>.json, 요약은 표준 출력.
"""
import json
import re
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from kotte import coach, runner, ollama  # noqa: E402

DATA, RES = ROOT / "eval" / "data", ROOT / "eval" / "results"
HANGUL = re.compile(r"[가-힣]")
LINE_RE = re.compile(r"(\d+)\s*번\s*줄")


def det():
    bugs = json.loads((DATA / "bugs1.json").read_text())
    rows = []
    for b in bugs:
        t = time.perf_counter()
        r = runner.check(b["code"], b["pid"], repair=True)
        fs = coach.facts(r)
        rep = (r.get("repair") or {})
        fixes = rep.get("fixes", [])
        d = coach.diagnose(b["pid"], b["code"], r, fs) if (fixes or (fs and fs[0]["kind"] in ("timeout", "error", "syntax"))) else None
        rows.append({"pid": b["pid"], "tier": d["tier"] if d else "llm 필요", "line_ok": bool(d and d.get("line") in b["lines"]),
                     "line": d.get("line") if d else None, "bug_lines": b["lines"], "fact": fs[0]["kind"] if fs else None,
                     "fix_ok": any(f["line"] in b["lines"] for f in fixes), "n_fixes": len(fixes),
                     "repair_ms": rep.get("ms"), "total_ms": (time.perf_counter() - t) * 1000})
    n = len(rows)
    by = {}
    for r in rows:
        by[r["tier"]] = by.get(r["tier"], 0) + 1
    print(f"1군데 버그 {n}개")
    print("진단 단계:", by)
    rep_rows = [r for r in rows if r["tier"] == "repair"]
    print(f"수리 검색이 고친 비율 {len(rep_rows) / n:.0%}, 그중 버그 줄을 맞힌 비율 {sum(r['line_ok'] for r in rep_rows) / max(1, len(rep_rows)):.0%}")
    rule = [r for r in rows if r["tier"] == "rule"]
    print(f"규칙(오류·시간 초과) {len(rule)}개, 그중 줄을 맞힌 비율 {sum(r['line_ok'] for r in rule) / max(1, len(rule)):.0%}")
    print(f"검사+수리 시간 중앙값 {st.median(r['total_ms'] for r in rows):.0f}ms, 최대 {max(r['total_ms'] for r in rows):.0f}ms")
    RES.mkdir(exist_ok=True)
    (RES / "det.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))


def score_message(msg, b, d):
    lines_said = [int(x) for x in LINE_RE.findall(msg)]
    hang = len(HANGUL.findall(msg)) / max(1, len(re.sub(r"\s", "", msg)))
    fake = [l for l in lines_said if l not in b["lines"] and l != d.get("line")]
    # 고칠 값 말하기: 원래(정답) 쪽 값을 '바꾸/써' 와 함께 말하면 유출
    leak = None
    for lab in b["labels"]:
        orig = lab.split("→")[0].strip()
        if len(orig) <= 3 and re.search(re.escape(orig) + r"\s*(으?로|를|을)?\s*(바꾸|바꿔|고치|고쳐|써|쓰|사용)", msg):
            leak = lab
    return {"len": len(msg), "hangul": round(hang, 2), "question": "?" in msg, "lines_said": lines_said,
            "line_hit": any(l in b["lines"] for l in lines_said), "fake_line": bool(fake), "leak": leak,
            "code_like": bool(coach.CODEY.search(msg))}


def llm(n=30, tag="llm"):
    if not ollama.status()["model"]:
        print("모델이 아직 없다:", ollama.status())
        return
    bugs = json.loads((DATA / "bugs2.json").read_text())[:n]
    rows = []
    for i, b in enumerate(bugs):
        r = runner.check(b["code"], b["pid"], repair=True)
        fs = coach.facts(r)
        if not fs:
            continue
        t0 = time.perf_counter()
        first = []
        on_msg = lambda piece: first or first.append(time.perf_counter() - t0)
        d = coach.diagnose(b["pid"], b["code"], r, fs, on_message=on_msg)
        t_diag = time.perf_counter() - t0
        t = time.perf_counter()
        u = coach.say(b["pid"], b["code"], d, 0, [], [], on_message=on_msg)
        t_say = time.perf_counter() - t
        sc = score_message(u["message"], b, d)
        row = {"pid": b["pid"], "bug_lines": b["lines"], "labels": b["labels"], "tier": d["tier"],
               "diag_line": d.get("line"), "diag_line_ok": d.get("line") in b["lines"], "diag_cat": d.get("category"),
               "cat_ok": d.get("category") in b["categories"], "llm_conf": d.get("llm_conf"), "cause": d.get("secret"),
               "lesson": d.get("lesson"), "message": u["message"], "source": u["source"], "tries": u.get("tries"),
               "t_diag": round(t_diag, 2), "t_say": round(t_say, 2),
               "first_token_say": (u.get("meta") or {}).get("first_token_s"),
               "first_msg_char": round(first[0], 2) if first else None, "total": round(t_diag + t_say, 2), **sc}
        rows.append(row)
        print(f"[{i + 1}/{len(bugs)}] {b['pid']} 진단줄 {d.get('line')} (버그 {b['lines']}) {d.get('category')} "
              f"{t_diag:.1f}s+{t_say:.1f}s {u['source']} | {u['message'][:90]}", flush=True)
    summarize(rows)
    RES.mkdir(exist_ok=True)
    (RES / f"{tag}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))


def summarize(rows):
    n = len(rows)
    if not n:
        return
    pct = lambda k: f"{sum(bool(r[k]) for r in rows) / n:.0%}"
    given = [r for r in rows if r["diag_line"]]
    print(f"\n2군데 버그 {n}개")
    print(f"AI 진단: 줄을 짚은 비율 {len(given) / n:.0%}, 짚은 것 중 맞은 비율 {sum(r['diag_line_ok'] for r in given) / max(1, len(given)):.0%}, 분류 일치 {pct('cat_ok')}")
    print(f"말하기: AI 문장 {sum(r['source'] == 'ai' for r in rows) / n:.0%} (나머지 정해진 문장), 다시 쓴 비율 {sum((r['tries'] or 1) > 1 for r in rows) / n:.0%}")
    print(f"  질문으로 끝남 {pct('question')}, 버그 줄 언급 {pct('line_hit')}, 없는 줄 언급 {pct('fake_line')}, 유출 {pct('leak')}, 코드 섞임 {pct('code_like')}")
    print(f"  길이 중앙값 {st.median(r['len'] for r in rows)}자, 한글 비율 중앙값 {st.median(r['hangul'] for r in rows)}")
    fm = [r["first_msg_char"] for r in rows if r.get("first_msg_char")]
    print(f"시간: 전체 중앙값 {st.median(r['total'] for r in rows):.1f}s (최대 {max(r['total'] for r in rows):.1f}s), "
          f"학생이 첫 글자를 보는 시간 중앙값 {st.median(fm) if fm else 0:.1f}s")
    by = {}
    for r in rows:
        by.setdefault(r["tier"], []).append(r)
    for k, v in by.items():
        print(f"  {k}: {len(v)}개, 줄 적중 {sum(x['diag_line_ok'] for x in v) / len(v):.0%}, 전체 시간 중앙값 {st.median(x['total'] for x in v):.1f}s")


def say_eval(n=15, tag="say"):
    """1군데 버그(수리 검색이 정답 수정을 앎)에서 말하기만: 고칠 값을 흘리는지가 핵심."""
    import random
    bugs = json.loads((DATA / "bugs1.json").read_text())
    random.Random(1).shuffle(bugs)
    rows = []
    for b in bugs:
        if len(rows) >= n:
            break
        r = runner.check(b["code"], b["pid"], repair=True)
        fs = coach.facts(r)
        d = coach.diagnose(b["pid"], b["code"], r, fs, llm=False)
        if not d or d["tier"] != "repair":
            continue
        t0 = time.perf_counter()
        first = []
        u = coach.say(b["pid"], b["code"], d, on_message=lambda p: first or first.append(time.perf_counter() - t0))
        sc = score_message(u["message"], b, d)
        rows.append({"pid": b["pid"], "fix": d["secret"], "line": d["line"], "message": u["message"], "source": u["source"],
                     "tries": u.get("tries"), "total": round(time.perf_counter() - t0, 2),
                     "first": round(first[0], 2) if first else None, **sc})
        print(f"[{len(rows)}] {b['pid']} {d['line']}번 줄 {d['secret']} {u['source']} {rows[-1]['total']}s | {u['message'][:100]}", flush=True)
    n = len(rows)
    print(f"\n말하기(수리 단계) {n}개: AI {sum(r['source'] == 'ai' for r in rows)}, 다시 씀 {sum((r['tries'] or 1) > 1 for r in rows)}, "
          f"유출(평가 기준) {sum(bool(r['leak']) for r in rows)}, 질문 {sum(r['question'] for r in rows)}, 버그 줄 언급 {sum(r['line_hit'] for r in rows)}")
    print(f"시간 중앙값 {st.median(r['total'] for r in rows):.1f}s, 첫 글자 중앙값 {st.median(r['first'] or 0 for r in rows):.1f}s")
    (RES / f"{tag}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "det"
    if mode == "det":
        det()
    elif mode == "say":
        say_eval(int(sys.argv[2]) if len(sys.argv) > 2 else 15, sys.argv[3] if len(sys.argv) > 3 else "say")
    else:
        llm(int(sys.argv[2]) if len(sys.argv) > 2 else 30, sys.argv[3] if len(sys.argv) > 3 else "llm")
