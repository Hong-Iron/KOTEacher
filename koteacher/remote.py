"""외부 API 클라이언트 (표준 라이브러리만). ollama.chat과 같은 모양으로 부른다.

    OpenAI 호환(/chat/completions): OpenAI, Gemini, OpenRouter, Groq, LM Studio·vLLM 같은 서버
    Anthropic(/messages): Claude

코치 말은 스트리밍(SSE)으로 받아 조각마다 on_token을 부른다.
"""
import json
import time
import urllib.error
import urllib.request

from . import config

# 생각하는 모델(추론 모델)은 답하기 전에 토큰을 쓴다. 코치가 정한 짧은 한도로는 답이 비어 버리므로 넉넉히 준다
MIN_TOKENS = 2048


def _headers(c):
    from . import __version__
    ua = f"KOTEacher/{__version__}"  # 기본 파이썬 User-Agent는 일부 회사(Groq 등)의 방화벽이 막는다
    if c["kind"] == "anthropic":
        return {"x-api-key": c["key"], "anthropic-version": "2023-06-01", "content-type": "application/json", "User-Agent": ua}
    h = {"Content-Type": "application/json", "X-Title": "KOTEacher", "User-Agent": ua}
    if c["key"]:
        h["Authorization"] = f"Bearer {c['key']}"
    return h


def _explain(code, msg):
    """HTTP 오류를 사람이 읽을 말로."""
    low = msg.lower()
    if code in (401, 403) or "api key" in low or "api_key" in low:
        return "API 키가 맞지 않거나 권한이 없습니다"
    if code == 404 or "model" in low and ("not found" in low or "does not exist" in low):
        return "모델 이름이나 주소를 찾지 못했습니다"
    if code == 429:
        return "요청 한도를 넘었거나 크레딧이 없습니다"
    return f"API 오류 {code}"


def _open(url, body, c, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=_headers(c),
                                 method="POST" if body is not None else "GET")
    return urllib.request.urlopen(req, timeout=timeout, context=config.ssl_context())


def _sse(resp):
    """SSE 줄에서 data 부분(JSON)만 꺼낸다."""
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            return
        try:
            yield json.loads(data)
        except json.JSONDecodeError:
            continue


def chat(messages, schema=None, think=False, max_tokens=300, temperature=0.4, on_token=None, timeout=120, stop=None, conf=None):
    c = conf or config.api_conf()
    if not c["model"]:
        raise RuntimeError("외부 API의 모델 이름이 비어 있습니다")
    msgs = [dict(m) for m in messages]
    if schema:  # 형식 강제는 회사마다 달라서, 말로 요청하고 받은 글에서 JSON만 꺼낸다
        msgs[-1]["content"] += ("\n\n다음 JSON 스키마에 맞는 JSON 객체 하나로만 답하세요. 코드 블록이나 다른 말은 쓰지 않습니다.\n"
                                + json.dumps(schema, ensure_ascii=False))
    budget = max(max_tokens, MIN_TOKENS)
    if c["kind"] == "anthropic":
        url = c["base"] + "/messages"
        body = {"model": c["model"], "max_tokens": budget, "temperature": temperature, "stream": True,
                "system": "\n\n".join(m["content"] for m in msgs if m["role"] == "system"),
                "messages": [m for m in msgs if m["role"] != "system"]}
        if stop:
            body["stop_sequences"] = stop[:4]
    else:
        url = c["base"] + "/chat/completions"
        body = {"model": c["model"], "messages": msgs, "temperature": temperature, "stream": True}
        # OpenAI의 새 모델은 max_tokens 대신 max_completion_tokens만 받는다
        body["max_completion_tokens" if "api.openai.com" in c["base"] else "max_tokens"] = budget
        if stop:
            body["stop"] = stop[:4]

    t0 = time.perf_counter()
    for _ in range(4):  # 모델이 받지 않는 설정이 있으면 빼거나 바꿔 다시 보낸다
        try:
            resp = _open(url, body, c, timeout)
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "ignore")
            low = msg.lower()
            if e.code == 400 and "temperature" in low and "temperature" in body:
                body.pop("temperature")
            elif e.code == 400 and "max_tokens" in low and "max_tokens" in body:
                body["max_completion_tokens"] = body.pop("max_tokens")
            elif e.code == 400 and "stop" in low and ("stop" in body or "stop_sequences" in body):
                body.pop("stop", None), body.pop("stop_sequences", None)
            else:
                raise RuntimeError(f"{_explain(e.code, msg)}: {msg[:200]}") from None
        except urllib.error.URLError as e:
            raise RuntimeError(f"서버에 닿지 못했습니다: {e.reason}") from None
    else:
        raise RuntimeError("API가 요청을 받지 않았습니다")

    first, parts, meta, finish = None, [], {}, None
    with resp:
        for d in _sse(resp):
            piece = ""
            if c["kind"] == "anthropic":
                t = d.get("type")
                if t == "content_block_delta" and d.get("delta", {}).get("type") == "text_delta":
                    piece = d["delta"]["text"]
                elif t == "message_start":
                    meta["prompt_eval_count"] = (d.get("message", {}).get("usage") or {}).get("input_tokens")
                elif t == "message_delta":
                    meta["eval_count"] = (d.get("usage") or {}).get("output_tokens")
                    finish = d.get("delta", {}).get("stop_reason") or finish
                elif t == "error":
                    raise RuntimeError(f"API 오류: {d.get('error', {}).get('message', '')[:200]}")
            else:
                ch = (d.get("choices") or [{}])[0]
                piece = (ch.get("delta") or {}).get("content") or ""
                finish = ch.get("finish_reason") or finish
                if d.get("usage"):
                    meta["prompt_eval_count"] = d["usage"].get("prompt_tokens")
                    meta["eval_count"] = d["usage"].get("completion_tokens")
            if piece:
                if first is None:
                    first = time.perf_counter() - t0
                parts.append(piece)
                if on_token:
                    on_token(piece)
    text = "".join(parts)
    if not text and finish in ("length", "max_tokens"):
        raise RuntimeError("모델이 생각하는 데 토큰을 다 써서 답을 쓰지 못했습니다. 생각(추론)하지 않는 모델을 골라 주세요")
    if schema:
        text = _json_part(text)
    meta["first_token_s"] = first
    meta["total_s"] = time.perf_counter() - t0
    return text, meta


def _json_part(text):
    """코드 블록이나 앞뒤 말이 붙어 와도 첫 JSON 객체만 남긴다."""
    a, b = text.find("{"), text.rfind("}")
    return text[a:b + 1] if a >= 0 and b > a else text


def models(conf):
    """그 회사에서 쓸 수 있는 모델 이름 목록."""
    try:
        with _open(conf["base"] + "/models", None, conf, 15) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "ignore")
        raise RuntimeError(f"{_explain(e.code, msg)}: {msg[:200]}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"서버에 닿지 못했습니다: {e.reason}") from None
    items = data.get("data") or data.get("models") or []
    ids = [(m.get("id") or m.get("name") or "").removeprefix("models/") for m in items if isinstance(m, dict)]
    return sorted(i for i in ids if i)


def test(conf):
    """짧은 질문 하나로 키·모델·주소가 맞는지 본다."""
    t = time.perf_counter()
    text, meta = chat([{"role": "user", "content": "연결 확인입니다. '좋아요'라고만 답하세요."}], max_tokens=20,
                      temperature=0.0, conf=conf, timeout=60)
    return {"ok": True, "text": text.strip()[:80], "sec": round(time.perf_counter() - t, 2), "first": meta.get("first_token_s")}
