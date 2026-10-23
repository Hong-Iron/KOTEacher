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
        self.practiced = False     # 연습 검사(반례·코치)를 한 번이라도 봤나. 봤으면 실전 통과로 치지 않는다


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
        from . import config
        return {"problems": items, "ai": ollama.status(), "mode": self.mode, "exam": bool(config.settings().get("exam")),
                "exam_minutes": int(config.settings().get("exam_minutes") or 0),
                "mistakes": len(self.store.mistakes(limit=10000))}

    def open(self, pid, code_override=None, fresh=False):
        """fresh=True면 지난 코드 없이 빈 틀로 연다 (오답 다시 풀기)."""
        p = vault.problem(pid)
        pk = packs.load(pid)
        aid = self.store.start_attempt(pid, mode="retry" if fresh else "practice")
        self.s = Session(pid, aid)
        ladder = vault.hint_ladder(pid)
        code = template_code(pk["params"]) if fresh else code_override or self.store.last_code(pid) or template_code(pk["params"])
        self.s.code = code
        if ollama.status()["model"]:  # 공통 앞부분(규칙·문제·코드)을 미리 읽혀 두어 첫 코치 응답을 빠르게
            threading.Thread(target=coach.warm, args=(pid, code), daemon=True).start()
        return {
            "id": pid, "title": p["title"], "level": p["level"], "source": p["source"], "url": p["url"],
            "concepts": p["concepts"], "concept_files": p["concept_files"], "statement": vault.to_html(p["statement_md"]),
            "params": pk["params"],
            "examples": [{"args": a[1:-1].rstrip(","), "expected": o} for a, o in pk["examples"]],
            "hidden_total": len(pk["hidden"]),
            "ladder": [{"step": l["step"], "title": l["title"]} for l in ladder], "hints_max": vault.HINTS,
            "code": code, "template": template_code(pk["params"]),
            "mistakes": self.store.mistakes(pid),
        }

    def concepts(self):
        st = self.store.problem_status()
        return [c | {"solved": sum(st.get(pid) == "solved" for pid in c["problems"])} for c in vault.concepts()]

    def history(self, pid=None):
        titles = {p["id"]: p for p in vault.problems()}
        out = []
        for r in self.store.history(pid):
            p = titles.get(r["problem_id"], {})
            if r["result"] == "pass":
                res = "helped" if (r["hints_opened"] or 0) >= 2 or r["solution_viewed"] else "solved"
                if res == "solved" and r.get("mode") == "exam" and not r["hints_opened"]:
                    res = "exam"
            else:
                res = "viewed" if r["solution_viewed"] else "open"
            out.append(r | {"title": p.get("title", r["problem_id"]), "level": p.get("level"), "res": res,
                            "minutes": round(((r["ended"] or r["last_t"]) - r["started"]) / 60, 1)})
        return out

    def attempt(self, aid):
        d = self.store.attempt_detail(int(aid))
        for s in d["snapshots"]:
            try:
                sm = json.loads(s["summary"] or "{}")
            except Exception:
                sm = {}
            s["fact"] = (sm.get("facts") or [{}])[0]
            s["exam"], s["submit"] = sm.get("exam"), sm.get("submit")
        return d

    def _content_file(self, rel):
        from . import config
        f = (config.CONTENT / rel).resolve()
        if config.CONTENT.resolve() not in f.parents or f.suffix not in (".py", ".svg"):
            raise ValueError("열 수 없는 파일입니다")
        return f

    def code_file(self, rel):
        f = self._content_file(rel)
        text = f.read_text(encoding="utf-8")
        role = f.stem.rsplit("_", 1)[-1]
        return {"path": rel, "name": f.name, "kind": f.suffix[1:], "role": role, "text": text,
                "needs": [m for m in ("matplotlib", "numpy") if f"import {m}" in text or f"from {m}" in text]}

    def run_code(self, rel):
        """개념 코드를 별도 프로세스에서 돌린다 (검증·구현·실험 코드는 표준 라이브러리만 쓴다)."""
        import subprocess
        from . import config
        f = self._content_file(rel)
        t = time.time()
        try:
            proc = subprocess.run(config.child_cmd("run", str(f)), capture_output=True, timeout=60, cwd=str(f.parent), **config.child_kw())
            out = (proc.stdout + ("\n" + proc.stderr if proc.stderr.strip() else ""))[-6000:]
            ok = proc.returncode == 0
        except subprocess.TimeoutExpired:
            out, ok = "60초 안에 끝나지 않아 멈췄습니다.", False
        if not ok and ("No module named 'matplotlib'" in out or "No module named 'numpy'" in out):
            out += "\n\n이 코드는 그림을 그리는 데 matplotlib·numpy가 필요합니다. 그림은 이미 문서 안에 들어 있습니다."
        return {"ok": ok, "out": out.strip() or "(출력 없음)", "sec": round(time.time() - t, 2)}

    def roadmap(self):
        st = self.store.problem_status()
        return {"html": vault.roadmap(), "status": st, "concepts": len(vault.concepts()), "problems": len(vault.problems()),
                "solved": sum(v == "solved" for v in st.values()), "helped": sum(v == "helped" for v in st.values())}

    def concept(self, name):
        d = vault.concept_doc(name)
        titles = {p["id"]: p for p in vault.problems()}
        st = self.store.problem_status()
        d["problem_list"] = [{"id": pid, "title": titles[pid]["title"], "level": titles[pid]["level"],
                              "status": st.get(pid, "new")} for pid in d.get("problems", [])]
        return d

    def set_mode(self, mode):
        self.mode = mode
        return mode

    def ai_status(self):
        return ollama.status()

    def setup_info(self):
        st = ollama.status()
        return {**st, "recommend": ollama.recommend(), "download": "https://ollama.com/download",
                "local": ollama.local_status() if st.get("external") else None}

    def set_coach_model(self, choice):
        """'auto' | 'accurate' | 'fast' | 'custom'. 바꾸면 지금 모델을 내리고 새 모델을 뒤에서 올린다."""
        from . import config
        before = config.MODEL
        config.save_settings(coach_model=choice, provider="ollama")
        st = ollama.status()
        if st["model"] and config.MODEL != before:
            def swap():
                config.MODEL, cur = before, config.MODEL
                ollama.unload()
                config.MODEL = cur
                ollama.load()
                self._push("model_ready", ollama.status())
            threading.Thread(target=swap, daemon=True).start()
        return st

    # ------------------------------------------------------------ 외부 API와 다른 Ollama 모델
    def api_settings(self):
        """회사별 설정. 키는 끝 네 글자만 보여 준다."""
        from . import config
        out = {}
        for p, d in config.PROVIDERS.items():
            c = config.api_conf(p)
            out[p] = {"label": d["label"], "base": c["base"], "default_base": d["base"], "model": c["model"],
                      "key_url": d["key_url"], "key": ("••••" + c["key"][-4:]) if c["key"] else ""}
        return {"provider": config.provider(), "providers": out}

    def _conf(self, provider, base=None, key=None, model=None):
        from . import config
        c = config.api_conf(provider)
        if base:
            c["base"] = base.strip().rstrip("/")
        if key and not key.startswith("••••"):
            c["key"] = key.strip()
        if model:
            c["model"] = model.strip()
        return c

    def api_models(self, provider, base=None, key=None):
        from . import remote
        try:
            return {"ok": True, "models": remote.models(self._conf(provider, base, key))}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    def api_test(self, provider, base=None, key=None, model=None):
        from . import remote
        try:
            return remote.test(self._conf(provider, base, key, model))
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    def save_api(self, provider, base=None, key=None, model=None):
        """외부 API를 코치로 쓴다. 키를 비워 두면 저장된 키를 그대로 쓴다."""
        from . import config
        c = self._conf(provider, base, key, model)
        api = dict(config.settings().get("api") or {})
        saved = dict(api.get(provider) or {})
        saved.update(base=c["base"], model=c["model"])
        if key and not key.startswith("••••"):
            saved["key"] = key.strip()
        api[provider] = saved
        was_local = not ollama.external()
        config.save_settings(api=api, provider=provider)
        if was_local:  # 내 컴퓨터 모델은 이제 안 쓰므로 메모리를 비운다
            threading.Thread(target=ollama.unload, daemon=True).start()
        return ollama.status()

    def use_local(self):
        """코치를 다시 내 컴퓨터의 Ollama로."""
        from . import config
        config.save_settings(provider="ollama")
        st = ollama.status()
        if st["model"] and not st["loaded"]:
            threading.Thread(target=lambda: (ollama.load(), self._push("model_ready", ollama.status())), daemon=True).start()
        return st

    def set_ollama_model(self, name):
        """받아 둔 다른 Ollama 모델(또는 받을 모델)을 이름으로 고른다. 없으면 받는다."""
        from . import config
        name = name.strip()
        if ":" not in name:
            name += ":latest"
        config.save_settings(provider="ollama")
        installed = ollama.status().get("installed") or []  # 지금 쓰는 모델(config.MODEL)도 여기서 정해진다
        config.save_settings(ollama_model=name)
        if name not in installed:
            config.save_settings(coach_model="custom")
            self.pull_model(name)
            return {"pulling": True, "name": name}
        self.set_coach_model("custom")
        return ollama.status()

    def pull_model(self, model):
        """모델을 받는다. 진행은 'pull' 이벤트로, 끝나면 'pull_done'."""
        def work():
            last = [0.0]

            def prog(status, done, total):
                now = time.time()
                if now - last[0] > 0.25 or (total and done >= total):
                    last[0] = now
                    self._push("pull", {"status": status, "done": done, "total": total})
            try:
                ollama.pull(model, prog)
                import koteacher.config as cfg
                if model not in cfg.MODELS:
                    cfg.MODELS.insert(0, model)
                st = ollama.status()
                if st["model"]:
                    ollama.load()
                self._push("pull_done", {"ok": True, "status": ollama.status()})
            except Exception as e:
                self._push("pull_done", {"ok": False, "error": str(e)[:200]})
        threading.Thread(target=work, daemon=True).start()
        return True

    # ------------------------------------------------------------ 힌트
    def hint(self, step):
        s = self.s
        step = int(step)
        final = vault.HINTS + 1  # 풀이 보기
        if step > s.hints + 1 and step < final:
            step = s.hints + 1
        lad = vault.hint_ladder(s.pid)
        if step < final:
            s.hints = max(s.hints, step)
            self.store.update_attempt(s.aid, hints_opened=s.hints)
        else:
            s.solution_viewed = True
            self.store.update_attempt(s.aid, solution_viewed=1)
            if s.open_fail:
                self._record_mistake(fixed=False, code_after=None)
        return {"step": step, "html": lad[step - 1]["html"], "hints": s.hints}

    # ------------------------------------------------------------ 다시 풀기와 추천
    def recommend(self):
        """홈의 추천. retry: 틀렸거나 힌트로 넘긴 문제(오래된 것 먼저), next: 약한 개념의 아직 안 푼 문제."""
        probs = {p["id"]: p for p in vault.problems()}
        st = self.store.problem_status()
        rows = self.store.rows("""
            SELECT a.problem_id pid, MAX(s.t) last_t, COUNT(s.id) runs,
                   MAX(CASE WHEN a.result='pass' AND COALESCE(a.hints_opened,0)<=1 AND NOT a.solution_viewed THEN s.t END) clean_t
            FROM attempts a JOIN snapshots s ON s.attempt_id=a.id GROUP BY a.problem_id""")
        last = {r["pid"]: r for r in rows}
        mis = self.store.rows("SELECT problem_id pid, COUNT(*) n, MAX(t) t, MAX(category) cat FROM mistakes GROUP BY problem_id")
        mis = {r["pid"]: r for r in mis}
        now = time.time()

        def ago(t):
            d = (now - t) / 86400
            return "오늘" if d < 1 else f"{int(d)}일 전"

        retry = []
        for pid, r in last.items():
            if pid not in probs:
                continue
            m = mis.get(pid)
            # 마지막 오답 뒤에 깨끗하게(힌트 1개 이하) 통과했으면 뺀다
            if m and r["clean_t"] and r["clean_t"] > m["t"]:
                continue
            why = (f"오답 {m['n']}번" + (f" · {m['cat']}" if m["cat"] else "")) if m else \
                {"helped": "힌트로 통과", "tried": "풀다 멈춤"}.get(st.get(pid))
            if not why or (not m and st.get(pid) == "tried" and r["runs"] < 3):  # 한두 번 열어 본 것은 빼고
                continue
            retry.append({"id": pid, "title": probs[pid]["title"], "level": probs[pid]["level"],
                          "why": f"{why} · {ago(r['last_t'])}", "score": (m["n"] if m else 0) * 2 + (now - r["last_t"]) / 86400})
        retry.sort(key=lambda x: -x["score"])

        # 약한 개념: 오답과 힌트로 넘긴 문제가 걸린 개념에 점수
        weak = {}
        for pid in set(mis) | {p for p, v in st.items() if v in ("helped", "tried")}:
            for c in probs.get(pid, {}).get("concepts", []):
                weak[c] = weak.get(c, 0) + (mis[pid]["n"] if pid in mis else 1)
        fresh = [p for p in probs.values() if st.get(p["id"], "new") == "new"]
        nxt, seen = [], set()
        for c, _ in sorted(weak.items(), key=lambda kv: -kv[1]):
            cand = sorted((p for p in fresh if c in p["concepts"] and p["id"] not in seen), key=lambda p: (p["level"], p["num"]))
            if cand:
                p = cand[0]; seen.add(p["id"])
                nxt.append({"id": p["id"], "title": p["title"], "level": p["level"], "why": f"약한 개념: {c}"})
            if len(nxt) >= 3:
                break
        if len(nxt) < 3:  # 기록이 적으면 로드맵 순서대로 아직 안 푼 쉬운 문제
            for p in sorted(fresh, key=lambda p: (p["level"], p["num"])):
                if p["id"] not in seen and len(nxt) < 3:
                    seen.add(p["id"])
                    nxt.append({"id": p["id"], "title": p["title"], "level": p["level"], "why": "아직 안 푼 문제 · " + ", ".join(p["concepts"][:2])})
        return {"retry": [{k: v for k, v in r.items() if k != "score"} for r in retry[:3]], "next": nxt}

    # ------------------------------------------------------------ 정보 창
    REPO = "Hong-Iron/KOTEacher"

    def about(self):
        import platform
        from . import __version__, config
        st = ollama.status()
        return {"version": __version__, "problems": len(vault.problems()), "concepts": len(vault.concepts()),
                "coach": (f"{st['external']} · {st['name']}" if st.get("external") else st.get("name")) if st.get("model") else None,
                "data": str(config.DATA), "os": f"{ {'Darwin': 'macOS', 'Windows': 'Windows'}.get(platform.system(), platform.system())} {platform.machine()}",
                "python": platform.python_version(), "repo": f"https://github.com/{self.REPO}"}

    def check_update(self):
        """GitHub의 최신 릴리스와 견준다 (누를 때만 인터넷에 묻는다)."""
        import urllib.request
        from . import __version__, config
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/{self.REPO}/releases/latest",
                                         headers={"Accept": "application/vnd.github+json", "User-Agent": "KOTEacher"})
            with urllib.request.urlopen(req, timeout=8, context=config.ssl_context()) as r:
                d = json.load(r)
        except Exception as e:
            return {"ok": False, "error": str(e)[:160]}
        latest = d.get("tag_name", "").lstrip("v")
        num = lambda v: tuple(int(x) for x in v.split(".") if x.isdigit())
        return {"ok": True, "latest": latest, "newer": num(latest) > num(__version__), "url": d.get("html_url")}

    # ------------------------------------------------------------ 타이핑 중 정적 검사
    def lint(self, code):
        """정의되지 않은 이름, 쓰지 않는 import 같은 것을 실행 없이 찾는다 (실전 모드에서는 화면이 부르지 않는다)."""
        from . import lint
        try:
            return lint.lint(code)
        except Exception as e:  # 검사기가 실패해도 편집은 계속된다
            return [{"line": 1, "col": 1, "end": 2, "severity": "info", "msg": f"검사기 오류: {e}"[:200]}]

    # ------------------------------------------------------------ 실전 모드
    def set_exam(self, on):
        """실전 모드: 자동 검사·코치·힌트를 끄고, 예시 실행과 제출(통과 개수만)만 쓴다. 다음에 켤 때도 유지한다."""
        from . import config
        config.save_settings(exam=bool(on))
        return bool(on)

    def set_exam_minutes(self, minutes):
        from . import config
        config.save_settings(exam_minutes=int(minutes or 0))
        return int(minutes or 0)

    def exam_overtime(self):
        """제한 시간이 끝난 뒤에도 계속 풀면, 그 뒤의 통과는 실전 통과로 치지 않는다."""
        if self.s:
            self.s.practiced = True
            self.store.snapshot(self.s.aid, self.s.code, {"exam": "timeup"}, False)
        return True

    def exam_run(self, code, kind, info=None):
        """kind='examples'면 예시만, 'submit'이면 숨은 검사를 끝까지 돌려 개수만 낸다. 코치·오답 기록은 쓰지 않는다."""
        s = self.s
        with self.lock:
            s.gen += 1  # 뒤에서 돌던 코치 응답은 버린다
            s.code = code
        only = "submit" if kind == "submit" else "examples"
        res = runner.check(code, s.pid, only=only)
        sub = res.get("submit")
        ex_ok = bool(res.get("examples")) and all(e["ok"] for e in res["examples"])
        ok = bool(sub) and ex_ok and sub["passed"] == sub["total"]
        self.store.snapshot(s.aid, code, {"exam": only, "submit": sub, **(info or {})}, ok)
        if ok:
            self.store.update_attempt(s.aid, result="pass", ended=time.time(), code=code,
                                      mode="practice" if s.practiced else "exam")
        return {"result": res, "passed": ok, "kind": only}

    # ------------------------------------------------------------ 검사와 코치
    def check(self, code, trigger="run"):
        s = self.s
        with self.lock:
            s.gen += 1
            gen = s.gen
            s.code = code
        res = runner.check(code, s.pid)
        s.practiced = True
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
        quick = bool((res.get("repair") or {}).get("fixes"))
        diag = coach.diagnose(s.pid, code, res, fs) if quick else None
        decision = None
        if diag:
            s.diag = diag
            self._open_fail(code, diag)
            # 확인된 진단이면 정해진 문장을 바로 보여 주고, AI 문장이 준비되면 그 자리를 바꾼다
            decision = s.policy.decide(self.mode, trigger, diag)
            out["decision"] = decision
            if decision == "speak":
                out["instant"] = coach.template(diag)
        out["diag"] = self._diag_public(diag) if diag else {"pending": True, "fact": fs[0]}
        threading.Thread(target=self._coach_bg, args=(gen, code, res, fs, trigger, diag, decision), daemon=True).start()
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

    def _streamer(self, gen):
        def emit(piece):
            if gen == self.s.gen:
                self._push("stream", {"gen": gen, "text": piece})
        return emit

    def _coach_bg(self, gen, code, res, fs, trigger, diag, decision=None):
        s = self.s
        try:
            if diag is None:
                # 한 군데 수정으로 안 고쳐짐 → AI가 진단과 말하기를 한 번에. 먼저 말해도 되는 상황이면 글자를 흘려 보낸다
                live = self.mode != "quiet" and (trigger == "run" or self.mode == "active")
                self._push("thinking", {"gen": gen})
                diag = coach.diagnose(s.pid, code, res, fs, llm=self.mode != "quiet", hint_level=s.hints,
                                      history=s.history, weak=self.store.weak_categories(),
                                      on_message=self._streamer(gen) if live else None)
                if gen != s.gen:
                    return
                s.diag = diag
                self._open_fail(code, diag)
                self._push("diag", {"gen": gen, "diag": self._diag_public(diag)})
            if decision is None:
                decision = s.policy.decide(self.mode, trigger, diag)
            if decision != "speak":
                self._push("chip", {"gen": gen, "diag": self._diag_public(diag)})
                return
            self._speak(gen, code, diag, trigger)
        except Exception as e:  # 코치가 실패해도 검사 결과는 이미 화면에 있다
            self._push("coach_error", {"gen": gen, "error": str(e)[:300]})

    def _speak(self, gen, code, diag, trigger):
        s = self.s
        if not diag.get("said"):
            self._push("thinking", {"gen": gen})
        t = time.time()
        u = coach.say(s.pid, code, diag, s.hints, s.history, self.store.weak_categories(), on_message=self._streamer(gen))
        if gen != s.gen:
            return
        diag.pop("said", None)  # 같은 말을 두 번 쓰지 않는다
        s.policy.spoke(trigger, diag)
        s.history.append(u["message"])
        mid = self.store.coach_msg(s.aid, signal=diag["fact"].get("kind"), tier=diag["tier"], hint_level=s.hints,
                                   message=u["message"], line=diag.get("line"), ms=int((time.time() - t) * 1000))
        self._push("say", {"gen": gen, "id": mid, "message": u["message"], "kind": u["kind"], "source": u["source"],
                           "line": diag.get("line"), "diag": self._diag_public(diag),
                           "first_token_s": (u.get("meta") or {}).get("first_token_s")})

    def prewarm(self, code):
        """타이핑이 잠깐 멈추면 지금 코드로 공통 앞부분을 미리 읽혀 둔다. 이어서 도는 검사의 코치 응답이 빨라진다."""
        s = self.s
        if not s or self.mode == "quiet" or getattr(self, "_warming", False) or getattr(s, "warmed", None) == code:
            return False
        if not ollama.status().get("loaded"):
            return False

        def work():
            self._warming = True
            try:
                coach.warm(s.pid, code)
                s.warmed = code
            finally:
                self._warming = False
        threading.Thread(target=work, daemon=True).start()
        return True

    def explain(self):
        """접힌 칩을 눌렀을 때: 규칙과 상관없이 지금 진단을 말한다."""
        s = self.s
        if not s.diag:
            return False
        gen, diag, code = s.gen, s.diag, s.code

        def work():
            d = diag
            # 조용히 모드라 AI 진단을 건너뛰었던 경우: 지금 진단한다
            if d["tier"] == "rule" and not d.get("line") and d["fact"].get("kind") in ("wrong", "timeout"):
                res = runner.check(code, s.pid)
                fs = coach.facts(res)
                if fs:
                    d = coach.diagnose(s.pid, code, res, fs, hint_level=s.hints, history=s.history,
                                       weak=self.store.weak_categories(), on_message=self._streamer(gen))
                    s.diag = d
            self._speak(gen, code, d, "ask")

        self._push("thinking", {"gen": gen})
        threading.Thread(target=work, daemon=True).start()
        return True

    def ask(self, question, code):
        s = self.s
        s.code = code
        gen = s.gen

        def work():
            dyn = ""
            if s.diag:
                dyn = coach.evidence(s.diag["fact"], None, code, s.diag.get("line") if s.diag.get("confidence") == "확인됨" else None)
            ex = coach.extras(s.pid, s.hints, s.history, [])
            task = (f"[학생 질문] {question}\n학생 질문에 바로 답한다(머리말 없이). 규칙 1을 지킨다. "
                    "질문이 정답이나 고친 코드를 달라는 것이면, 왼쪽 힌트 사다리의 다음 단계를 열어 보라고 권한다.")
            msgs = coach.messages(s.pid, code, dyn + ("\n\n" + ex if ex else ""), task)
            t = time.time()
            try:
                text, meta = ollama.chat(msgs, max_tokens=220, on_token=coach.RawStream(self._streamer(gen)).feed)
                msg = coach.clean_raw(text)
                if coach.leak_reason(msg, s.diag or {}, s.pid):
                    msg = "그 부분은 직접 찾아야 실력이 돼요. 막히면 왼쪽 힌트 사다리의 다음 단계를 열어 보세요."
            except Exception as e:
                msg = f"코치가 지금 답할 수 없어요 ({str(e)[:80]}). Ollama가 켜져 있는지 확인해 주세요."
            mid = self.store.coach_msg(s.aid, signal="ask", tier="ask", hint_level=s.hints, message=msg,
                                       ms=int((time.time() - t) * 1000))
            s.history.append(msg)
            self._push("answer", {"gen": gen, "id": mid, "q": question, "message": msg})

        threading.Thread(target=work, daemon=True).start()
        return True

    # ------------------------------------------------------------ 문서에서 골라 묻기
    DOC_SYSTEM = ("너는 알고리즘을 쉽게 설명하는 선배다. 부드러운 존댓말. 학생이 문서에서 고른 부분과 그 문단을 보고 질문에 답한다.\n"
                  "- 인사말이나 칭찬 없이 바로 답한다. 쉬운 한국어로 3~5문장. 필요하면 작은 숫자 예를 하나 든다.\n"
                  "- 문서에 있는 내용과 어긋나는 말을 지어내지 않는다.\n"
                  "- 학생이 지금 풀고 있는 문제의 정답 코드는 쓰지 않는다.\n"
                  "- 고른 부분이 코드면, 그 줄이 무엇을 하는지와 왜 그렇게 쓰는지를 설명한다. 필요하면 작은 입력으로 값이 어떻게 바뀌는지 보여 준다.")

    def ask_doc(self, rid, quote, context, doc, question, prefix="", code=""):
        """고른 부분에 대해 묻는다. 답은 doc_stream으로 흘려 보내고, 끝나면 기록해 doc_answer로 알린다."""
        def work():
            title = ""
            if doc and doc.startswith("problem:"):
                title = "문제 " + vault.problem(doc.split(":", 1)[1])["title"]
            elif doc and doc.startswith("code:"):
                title = "개념 코드 " + doc.split("/")[-1]
            elif doc:
                title = "개념 문서 " + doc.split(".", 1)[-1]
            where = "그 부분의 코드" if (doc or "").startswith("code:") or context.startswith("(코드 ") else "그 문단"
            user = f"[{title}]\n[고른 부분] {quote}\n\n[{where}]\n{context}\n\n[질문] {question}"
            if code.strip() and self.s:
                user += f"\n\n[학생이 지금 쓰는 코드, 참고만]\n{code[:1500]}"
            pieces = []

            def emit(t):
                pieces.append(t)
                self._push("doc_stream", {"id": rid, "text": t})
            try:
                text, _ = ollama.chat([{"role": "system", "content": self.DOC_SYSTEM}, {"role": "user", "content": user}],
                                      max_tokens=320, temperature=0.4, on_token=emit)
                msg = coach.tidy(text)
                if self.s and coach.leak_reason(msg, {}, self.s.pid) == "모범 풀이 코드와 겹침":
                    msg = "그 부분은 지금 푸는 문제의 답과 너무 가까워서 말하지 않을게요. 왼쪽 힌트 사다리를 한 단계 열어 보세요."
            except Exception as e:
                msg = f"코치가 지금 답할 수 없어요 ({str(e)[:80]}). Ollama가 켜져 있는지 확인해 주세요."
                self._push("doc_answer", {"id": rid, "message": msg, "note": None})
                return
            nid = self.store.add_note(doc, quote, prefix, question, msg)
            self._push("doc_answer", {"id": rid, "message": msg, "note": nid})

        threading.Thread(target=work, daemon=True).start()
        return True

    def search(self, q):
        """전체 검색. 띄어 쓴 낱말은 모두 들어 있어야 한다(대소문자 무시)."""
        import re as _re
        terms = [t.lower() for t in q.split() if t.strip()]
        if not terms:
            return {}
        hit = lambda *xs: all(any(t in (x or "").lower() for x in xs) for t in terms)

        def snip(text):
            low = text.lower()
            i = min((low.find(t) for t in terms if t in low), default=-1)
            if i < 0:
                return ""
            a = max(0, i - 40)
            return ("…" if a else "") + _re.sub(r"\s+", " ", text[a:i + 80]) + "…"

        st = self.store.problem_status()
        out = {"problems": [], "concepts": [], "content": [], "notes": [], "mistakes": []}
        for p in vault.problems():
            if hit(p["title"], p["source"], " ".join(p["concepts"]), p["id"]):
                out["problems"].append({"id": p["id"], "title": p["title"], "level": p["level"], "sub": p["source"],
                                        "status": st.get(p["id"], "new")})
        for c in vault.concepts():
            if hit(c["title"], c["aliases"]):
                out["concepts"].append({"name": c["name"], "title": c["title"], "sub": c["summary"]})
        for it in vault.search_index():
            if hit(it["text"]):
                low = it["text"].lower()
                out["content"].append({"kind": it["kind"], "key": it["key"], "title": it["title"], "snippet": snip(it["text"]),
                                       "count": sum(low.count(t) for t in terms), "term": terms[0],
                                       "boost": sum(t in it["title"].lower() for t in terms)})
        out["content"].sort(key=lambda r: (-r.pop("boost"), -r["count"]))  # 제목에 검색어가 있으면 앞으로
        for n in self.store.rows("SELECT * FROM doc_notes ORDER BY t DESC"):
            if hit(n["quote"], n["question"], n["answer"]):
                title = (vault.problem(n["doc"].split(":", 1)[1])["title"] if n["doc"].startswith("problem:")
                         else n["doc"].split("/")[-1] if n["doc"].startswith("code:")
                         else n["doc"].split(".", 1)[-1])
                out["notes"].append({"id": n["id"], "doc": n["doc"], "title": title, "question": n["question"],
                                     "snippet": snip(n["answer"]) or n["answer"][:100]})
        for m in self.mistakes(None):
            if hit(m["name"], m["note"], m["category"], m["title"], m["evidence"]):
                out["mistakes"].append({"pid": m["problem_id"], "title": m["title"], "name": m["name"], "category": m["category"]})
        for k in out:
            out[k] = out[k][:30 if k == "content" else 12]
        return out

    def doc_notes(self, doc):
        return self.store.notes(doc)

    def delete_note(self, nid):
        self.store.delete_note(int(nid))
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
