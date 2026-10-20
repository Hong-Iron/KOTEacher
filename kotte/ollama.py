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
    """서버가 떠 있는지, 모델이 받아져 있는지."""
    try:
        with urllib.request.urlopen(config.OLLAMA + "/api/tags", timeout=2) as r:
            names = [m["name"] for m in json.load(r).get("models", [])]
        return {"server": True, "model": config.MODEL in names, "name": config.MODEL}
    except Exception:
        return {"server": False, "model": False, "name": config.MODEL}


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
