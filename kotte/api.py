"""화면(JS)에서 부르는 함수들. pywebview가 window.pywebview.api.<이름>으로 노출한다."""
import difflib
import json
import threading
import time

from . import coach, ollama, packs, runner, vault
from .store import Store


def template_code(params):
    return f"def solution({', '.join(params)}):\n    answer = 0\n    return answer\n"


class Session:
    def __init__(self, pid, aid):
        self.pid, self.aid = pid, aid
        self.hints = 0
        self.solution_viewed = False
        self.policy = coach.Policy()
        self.history = []          # 코치가 한 말
        self.open_fail = None      # 아직 못 고친 실패 (오답 기록 후보)
        self.diag = None           # 마지막 진단
        self.code = ""
        self.gen = 0


class Api:
    def __init__(self):
        self.store = Store()
        self.window = None
        self.s = None
        self.mode = "normal"
        self.lock = threading.Lock()

    # ------------------------------------------------------------ 화면으로 보내기
    def _push(self, event, data):
        if self.window:
            self.window.evaluate_js(f"window.KG && KG.on({json.dumps(event)}, {json.dumps(data, ensure_ascii=False)})")

    # ------------------------------------------------------------ 목록과 열기
    def boot(self):
        st = self.store.problem_status()
        items = [{k: p[k] for k in ("id", "title", "level", "source", "concepts", "num")} | {"status": st.get(p["id"], "new")}
                 for p in vault.problems()]
        return {"problems": items, "ai": ollama.status(), "mode": self.mode,
                "mistakes": len(self.store.mistakes(limit=10000))}

    def open(self, pid):
        p = vault.problem(pid)
        pk = packs.load(pid)
        aid = self.store.start_attempt(pid)
        self.s = Session(pid, aid)
        ladder = vault.hint_ladder(pid)
        code = self.store.last_code(pid) or template_code(pk["params"])
        self.s.code = code
        return {
            "id": pid, "title": p["title"], "level": p["level"], "source": p["source"], "url": p["url"],
            "concepts": p["concepts"], "statement": vault.to_html(p["statement_md"]),
            "params": pk["params"],
            "examples": [{"args": a[1:-1].rstrip(","), "expected": o} for a, o in pk["examples"]],
            "hidden_total": len(pk["hidden"]),
            "ladder": [{"step": l["step"], "title": l["title"]} for l in ladder],
            "code": code, "template": template_code(pk["params"]),
            "mistakes": self.store.mistakes(pid),
        }

    def set_mode(self, mode):
        self.mode = mode
        return mode

    def ai_status(self):
        return ollama.status()

    # ------------------------------------------------------------ 힌트
    def hint(self, step):
        s = self.s
        step = int(step)
        if step > s.hints + 1 and step < 5:
            step = s.hints + 1
        lad = vault.hint_ladder(s.pid)
        if step <= 4:
            s.hints = max(s.hints, step)
            self.store.update_attempt(s.aid, hints_opened=s.hints)
        else:
            s.solution_viewed = True
            self.store.update_attempt(s.aid, solution_viewed=1)
            if s.open_fail:
                self._record_mistake(fixed=False, code_after=None)
        return {"step": step, "html": lad[step - 1]["html"], "hints": s.hints}

    # ------------------------------------------------------------ 검사와 코치
    def check(self, code, trigger="run"):
        s = self.s
        with self.lock:
            s.gen += 1
            gen = s.gen
            s.code = code
        res = runner.check(code, s.pid)
        fs = coach.facts(res)
        ok = coach.passed(res)
        self.store.snapshot(s.aid, code, {"facts": fs[:3]}, ok)
        out = {"result": res, "passed": ok, "facts": fs[:5]}
        risk = coach.complexity_risk(code, vault.problem(s.pid)["statement_md"])
        if risk:
            out["risk"] = risk

        if ok:
            self.store.update_attempt(s.aid, result="pass", ended=time.time(), code=code)
            if s.open_fail:
                out["mistake"] = self._record_mistake(fixed=True, code_after=code)
            s.diag = None
            return out

        if not fs or fs[0]["kind"] in ("syntax", "load", "fatal"):
            s.diag = coach.diagnose(s.pid, code, res, fs) if fs else None
            out["diag"] = self._diag_public(s.diag)
            out["decision"] = "chip"
            return out

        if coach.is_stub(code):  # 아직 풀이가 없으면 코치는 기다린다
            out["decision"] = "none"
            return out

        # 실패: 진단은 빠른 단계(규칙·수리)만 여기서 하고, AI 진단과 말하기는 뒤에서
        quick = bool((res.get("repair") or {}).get("fixes")) or (fs[0]["kind"] == "error" and fs[0].get("line"))
        diag = coach.diagnose(s.pid, code, res, fs) if quick else None
        if diag:
            s.diag = diag
            self._open_fail(code, diag)
        out["diag"] = self._diag_public(diag) if diag else {"pending": True, "fact": fs[0]}
        threading.Thread(target=self._coach_bg, args=(gen, code, res, fs, trigger, diag), daemon=True).start()
        return out

    def _diag_public(self, d):
        if not d:
            return None
        return {k: d.get(k) for k in ("tier", "category", "line", "confidence", "fact")}

    def _open_fail(self, code, diag):
        s = self.s
        if s.open_fail is None:
            s.open_fail = {"t": time.time(), "hints": s.hints}
        s.open_fail.update(code=code, diag=diag)

    def _coach_bg(self, gen, code, res, fs, trigger, diag):
        s = self.s
        try:
            if diag is None:
                self._push("thinking", {"gen": gen})
                diag = coach.diagnose(s.pid, code, res, fs)
                if gen != s.gen:
                    return
                s.diag = diag
                self._open_fail(code, diag)
                self._push("diag", {"gen": gen, "diag": self._diag_public(diag)})
            decision = s.policy.decide(self.mode, trigger, diag)
            if decision != "speak":
                self._push("chip", {"gen": gen, "diag": self._diag_public(diag)})
                return
            self._speak(gen, code, diag, trigger)
        except Exception as e:  # 코치가 실패해도 검사 결과는 이미 화면에 있다
            self._push("coach_error", {"gen": gen, "error": str(e)[:300]})

    def _speak(self, gen, code, diag, trigger):
        s = self.s
        self._push("thinking", {"gen": gen})
        t = time.time()
        u = coach.say(s.pid, code, diag, s.hints, s.history, self.store.weak_categories())
        if gen != s.gen:
            return
        s.policy.spoke(trigger, diag)
        s.history.append(u["message"])
        mid = self.store.coach_msg(s.aid, signal=diag["fact"].get("kind"), tier=diag["tier"], hint_level=s.hints,
                                   message=u["message"], line=diag.get("line"), ms=int((time.time() - t) * 1000))
        self._push("say", {"gen": gen, "id": mid, "message": u["message"], "kind": u["kind"], "source": u["source"],
                           "line": diag.get("line"), "diag": self._diag_public(diag),
                           "first_token_s": (u.get("meta") or {}).get("first_token_s")})

    def explain(self):
        """접힌 칩을 눌렀을 때: 규칙과 상관없이 지금 진단을 말한다."""
        s = self.s
        if not s.diag:
            return False
        gen = s.gen
        threading.Thread(target=self._speak, args=(gen, s.code, s.diag, "ask"), daemon=True).start()
        return True

    def ask(self, question, code):
        s = self.s
        s.code = code
        gen = s.gen

        def work():
            p = vault.problem(s.pid)
            ctx = f"[문제]\n{vault.plain(p['statement_md'])[:600]}\n\n[학생 코드]\n{coach.numbered(code)}"
            if s.diag:
                f = s.diag["fact"]
                ctx += f"\n\n[최근 검사] {f.get('where', '')} 입력 {f.get('args')} 기대 {f.get('expected')} 내 답 {f.get('got') or f.get('msg')}"
            hc = coach._hint_context(s.pid, s.hints)
            if hc:
                ctx += f"\n\n[학생이 연 힌트]\n{hc}"
            rules = coach.SAY_RULES.replace("[증거]에 있는 사실 하나에 대해서만 말한다", "학생 질문에 답하되, 질문이 정답을 달라는 것이면 힌트 사다리의 다음 단계를 열어 보라고 권한다")
            msgs = [{"role": "system", "content": rules}, {"role": "user", "content": ctx + f"\n\n[학생 질문] {question}"}]
            t = time.time()
            try:
                text, meta = ollama.chat(msgs, schema=coach.SAY_SCHEMA, max_tokens=260)
                msg = json.loads(text).get("message", "").strip()
                if coach.leak_reason(msg, s.diag or {}, s.pid):
                    msg = "그 부분은 직접 찾아야 실력이 돼요. 막히면 왼쪽 힌트 사다리의 다음 단계를 열어 보세요."
            except Exception as e:
                msg = f"코치가 지금 답할 수 없어요 ({str(e)[:80]}). Ollama가 켜져 있는지 확인해 주세요."
            mid = self.store.coach_msg(s.aid, signal="ask", tier="ask", hint_level=s.hints, message=msg,
                                       ms=int((time.time() - t) * 1000))
            s.history.append(msg)
            self._push("answer", {"gen": gen, "id": mid, "q": question, "message": msg})

        self._push("thinking", {"gen": gen})
        threading.Thread(target=work, daemon=True).start()
        return True

    def rate(self, mid, rating):
        self.store.rate(int(mid), rating)
        return True

    def save_code(self, code):
        if self.s:
            self.s.code = code
            self.store.update_attempt(self.s.aid, code=code)
        return True

    # ------------------------------------------------------------ 오답 기록
    def _record_mistake(self, fixed, code_after):
        s = self.s
        of, s.open_fail = s.open_fail, None
        d = of["diag"]
        before = of["code"]
        diff = ""
        if code_after is not None:
            diff = "\n".join(l for l in difflib.unified_diff(before.splitlines(), code_after.splitlines(), lineterm="", n=0)
                             if l[:1] in "+-" and not l.startswith(("+++", "---")))
        if d.get("tier") == "repair":
            name = f"{d['category']}: {d['line']}번 줄 {d['secret']}"
        else:
            name = d.get("lesson") or f"{d['category']} 실수"
        f = d["fact"]
        ev = f"{f.get('where', '')} 입력 {f.get('args')} → 기대 {f.get('expected')}, 내 답 {f.get('got') or f.get('msg')}"
        p = vault.problem(s.pid)
        row = dict(attempt_id=s.aid, problem_id=s.pid, concepts=json.dumps(p["concepts"], ensure_ascii=False),
                   category=d["category"], name=name[:120], signal=f.get("kind"), evidence=ev[:600], line=d.get("line"),
                   code_before=before, code_after=code_after, diff=diff, detected_by=d.get("tier"), fixed=int(fixed),
                   time_to_fix=time.time() - of["t"], hints_at_detection=of["hints"], note=None)
        row["id"] = self.store.add_mistake(**row)
        row["title"] = p["title"]
        if fixed and diff:
            threading.Thread(target=self._name_mistake, args=(row,), daemon=True).start()
        return row

    def _name_mistake(self, row):
        """고친 뒤라 답을 말해도 된다. 실수에 짧은 이름을 붙인다."""
        msgs = [{"role": "system", "content": "학생이 고친 코드 차이를 보고, 무엇을 틀렸는지 25자 안의 한국어 명사구로 이름을 붙인다. 예: '길이가 같을 때도 답을 바꿈', '방문 표시를 꺼낼 때 함'."},
                {"role": "user", "content": f"분류: {row['category']}\n증거: {row['evidence']}\n고친 차이:\n{row['diff'][:1200]}"}]
        try:
            text, _ = ollama.chat(msgs, schema={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
                                  max_tokens=60, temperature=0.2)
            name = json.loads(text)["name"].strip()[:60]
        except Exception:
            return
        if name:
            self.store._ex("UPDATE mistakes SET name=? WHERE id=?", (name, row["id"]))
            self._push("mistake_named", {"id": row["id"], "name": name})

    def note(self, mid, text):
        self.store.set_note(int(mid), text.strip()[:300])
        return True

    def mistakes(self, pid=None):
        rows = self.store.mistakes(pid)
        titles = {p["id"]: p["title"] for p in vault.problems()}
        for r in rows:
            r["title"] = titles.get(r["problem_id"], r["problem_id"])
        return rows

    def log(self, msg):
        """화면 쪽 상태를 앱 로그로 남긴다 (자가 점검용)."""
        import sys
        print(f"[ui] {msg}", file=sys.stderr, flush=True)
        return True
