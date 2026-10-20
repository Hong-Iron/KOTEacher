"""Ollama /api/chat 클라이언트 (표준 라이브러리만)."""
import json
import time
import urllib.error
import urllib.request

from . import config


def _post(path, body, timeout):
    req = urllib.request.Request(config.OLLAMA + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=timeout)


def status():
    """서버가 떠 있는지, 쓸 모델이 받아져 있는지. 후보 가운데 받아져 있는 첫 모델을 고른다."""
    try:
        with urllib.request.urlopen(config.OLLAMA + "/api/tags", timeout=2) as r:
            names = [m["name"] for m in json.load(r).get("models", [])]
    except Exception:
        return {"server": False, "model": False, "name": config.MODEL}
    pick = next((m for m in config.MODELS if m in names), None)
    if pick:
        config.MODEL = pick
    return {"server": True, "model": bool(pick), "name": config.MODEL, "loaded": bool(pick) and is_loaded(),
            "loading": _loading}


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


def chat(messages, schema=None, think=False, max_tokens=300, temperature=0.4, on_token=None, timeout=120):
    """답 전체 문자열과 측정값을 돌려준다. on_token이 있으면 조각마다 부른다."""
    body = {
        "model": config.MODEL, "messages": messages, "stream": True, "think": think,
        "keep_alive": "30m",
        "options": {"num_ctx": config.NUM_CTX, "num_predict": max_tokens, "temperature": temperature},
    }
    if schema:
        body["format"] = schema
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
