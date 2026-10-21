"""Ollama /api/chat 클라이언트 (표준 라이브러리만).

설정에서 외부 API를 고르면 chat·status가 remote.py로 넘긴다. 부르는 쪽은 어느 쪽인지 몰라도 된다.
"""
import json
import os
import time
import urllib.error
import urllib.request

from . import config


def _post(path, body, timeout):
    req = urllib.request.Request(config.OLLAMA + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=timeout)


def external():
    return config.provider() != "ollama"


def status():
    """서버가 떠 있는지, 쓸 모델이 받아져 있는지. 후보 가운데 받아져 있는 첫 모델을 고른다."""
    if external():  # 외부 API는 키와 모델 이름이 있으면 준비된 것으로 본다 (자주 불리므로 요청은 보내지 않는다)
        c = config.api_conf()
        ready = bool(c["model"]) and (bool(c["key"]) or c["provider"] == "custom")
        return {"server": ready, "model": ready, "name": c["model"], "loaded": ready, "loading": False,
                "choice": config.settings().get("coach_model", "auto"), "have": {}, "external": c["label"], "provider": c["provider"]}
    return local_status()


def local_status():
    """내 컴퓨터 Ollama의 상태 (외부 API를 쓰는 중에도 설정 화면에서 보여 준다)."""
    try:
        with urllib.request.urlopen(config.OLLAMA + "/api/tags", timeout=2) as r:
            names = [m["name"] for m in json.load(r).get("models", [])]
    except Exception:
        return {"server": False, "model": False, "name": config.MODEL}
    pick = next((m for m in candidates() if m in names), None)
    if pick:
        config.MODEL = pick
    have = {k: next((m for m in v["models"] if m in names), None) for k, v in config.CHOICES.items()}
    return {"server": True, "model": bool(pick), "name": config.MODEL, "loaded": bool(pick) and is_loaded(),
            "loading": _loading, "choice": config.settings().get("coach_model", "auto"), "have": have,
            "installed": names, "provider": "ollama"}


def candidates():
    """쓸 모델 후보 순서: 환경 변수 → 사용자 선택(정확도/속도) → 자동(메모리에 맞춘 추천 먼저)."""
    import os
    if os.environ.get("KOTEACHER_MODEL"):
        return [os.environ["KOTEACHER_MODEL"]]
    choice = config.settings().get("coach_model", "auto")
    if choice == "custom" and config.settings().get("ollama_model"):  # 사용자가 이름으로 고른 Ollama 모델
        return [config.settings()["ollama_model"]]
    if choice in config.CHOICES:
        other = "fast" if choice == "accurate" else "accurate"
        return config.CHOICES[choice]["models"] + config.CHOICES[other]["models"]
    first = recommend()["choice"]
    other = "fast" if first == "accurate" else "accurate"
    return config.CHOICES[first]["models"] + config.CHOICES[other]["models"]


_loading = False


def is_loaded():
    """모델이 지금 메모리에 올라와 있는지 (/api/ps)."""
    try:
        with urllib.request.urlopen(config.OLLAMA + "/api/ps", timeout=2) as r:
            return any(m.get("name") == config.MODEL or m.get("model") == config.MODEL for m in json.load(r).get("models", []))
    except Exception:
        return False


def load():
    """프롬프트 없이 요청하면 모델만 올린다. 앱이 켜져 있는 동안 내려가지 않게 keep_alive를 길게 준다."""
    global _loading
    if external():
        return
    _loading = True
    try:
        body = {"model": config.MODEL, "keep_alive": "30m", "options": {"num_ctx": config.NUM_CTX}}
        with _post("/api/generate", body, 300) as r:
            r.read()
    finally:
        _loading = False


def unload():
    try:
        with _post("/api/generate", {"model": config.MODEL, "keep_alive": 0}, 10) as r:
            r.read()
    except Exception:
        pass


def chat(messages, schema=None, think=False, max_tokens=300, temperature=0.4, on_token=None, timeout=120, stop=None):
    """답 전체 문자열과 측정값을 돌려준다. on_token이 있으면 조각마다 부른다."""
    if external():
        from . import remote
        return remote.chat(messages, schema=schema, max_tokens=max_tokens, temperature=temperature, on_token=on_token,
                           timeout=timeout, stop=stop)
    body = {
        "model": config.MODEL, "messages": messages, "stream": True, "think": think,
        "keep_alive": "30m",
        "options": {"num_ctx": config.NUM_CTX, "num_predict": max_tokens, "temperature": temperature},
    }
    if schema:
        body["format"] = schema
    if stop:
        body["options"]["stop"] = stop
    t0 = time.perf_counter()
    first = None
    parts, meta = [], {}
    try:
        resp = _post("/api/chat", body, timeout)
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="ignore")
        if "think" in msg and think is not None:  # 생각 모드를 모르는 모델이면 빼고 다시
            body.pop("think")
            resp = _post("/api/chat", body, timeout)
        else:
            raise RuntimeError(msg[:300])
    with resp:
        for line in resp:
            if not line.strip():
                continue
            d = json.loads(line)
            piece = d.get("message", {}).get("content", "")
            if piece:
                if first is None:
                    first = time.perf_counter() - t0
                parts.append(piece)
                if on_token:
                    on_token(piece)
            if d.get("done"):
                meta = {k: d.get(k) for k in ("prompt_eval_count", "eval_count", "eval_duration", "prompt_eval_duration")}
    meta["first_token_s"] = first
    meta["total_s"] = time.perf_counter() - t0
    return "".join(parts), meta


def ram_gb():
    try:
        if hasattr(os, "sysconf") and "SC_PHYS_PAGES" in os.sysconf_names:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2 ** 30
        import ctypes  # 윈도
        class M(ctypes.Structure):
            _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("t", ctypes.c_ulonglong)] + [(f"x{i}", ctypes.c_ulonglong) for i in range(6)]
        m = M(); m.l = ctypes.sizeof(M)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.t / 2 ** 30
    except Exception:
        return 0


def recommend():
    """자동 선택은 속도 우선(e4b)이다. 12B와 견주어 응답이 약 2배 빠르고(첫 글자 약 3배),
    버그 줄 적중은 같은 12문제에서 9/12로 12B(6/12)보다 낮지 않았다 (eval/ab_model.sh, 2026-10-21)."""
    gb = ram_gb()
    choice = "fast"
    c = config.CHOICES[choice]
    return {"model": c["models"][0], "size": c["size"], "ram": round(gb), "choice": choice}


def pull(model, on_progress):
    """모델 받기. on_progress(상태, 받은 바이트, 전체 바이트)."""
    with _post("/api/pull", {"model": model, "stream": True}, 3600) as r:
        for line in r:
            if line.strip():
                d = json.loads(line)
                if d.get("error"):
                    raise RuntimeError(d["error"])
                on_progress(d.get("status", ""), d.get("completed") or 0, d.get("total") or 0)
