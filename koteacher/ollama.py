"""Ollama /api/chat 클라이언트 (표준 라이브러리만).

설정에서 외부 API를 고르면 chat·status가 remote.py로 넘긴다. 부르는 쪽은 어느 쪽인지 몰라도 된다.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

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
    if choice in config.CHOICES:  # 고른 것을 먼저, 없으면 gemma(속도 → 정확도) 순. Ministral은 고른 경우에만 쓴다
        rest = [k for k in ("fast", "accurate") if k != choice]
        return config.CHOICES[choice]["models"] + [m for k in rest for m in config.CHOICES[k]["models"]]
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
    """모델 받기. on_progress(상태, 받은 바이트, 전체 바이트, 덩어리 digest)."""
    with _post("/api/pull", {"model": model, "stream": True}, 3600) as r:
        for line in r:
            if line.strip():
                d = json.loads(line)
                if d.get("error"):
                    raise RuntimeError(d["error"])
                on_progress(d.get("status", ""), d.get("completed") or 0, d.get("total") or 0, d.get("digest"))


# ---------------------------------------------------------------- 처음 실행: Ollama 찾기·켜기·설치
OLLAMA_ZIP = "https://ollama.com/download/Ollama-darwin.zip"  # install.sh와 같은 곳


def _host():
    u = urllib.parse.urlparse(config.OLLAMA)
    return u.hostname, u.port or 11434


def find():
    """설치된 Ollama. ('app', 앱 경로) 또는 ('cli', 실행 파일), 없으면 None.
    Finder에서 연 앱은 PATH가 짧아 Homebrew가 까는 곳을 직접 찾는다."""
    if sys.platform == "darwin":
        for p in (Path("/Applications/Ollama.app"), Path.home() / "Applications/Ollama.app"):
            if p.exists():
                return "app", p
    if os.name == "nt":
        p = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama app.exe"
        if p.exists():
            return "app", p
    for p in (shutil.which("ollama"), "/opt/homebrew/bin/ollama", "/usr/local/bin/ollama"):
        if p and Path(p).exists():
            return "cli", Path(p)
    return None


def start(wait=30):
    """설치돼 있는데 꺼져 있으면 켜고, 서버가 뜰 때까지 기다린다. 떴으면 True.
    다른 컴퓨터의 Ollama(KOTEACHER_OLLAMA)를 쓰는 중이면 켜지 않는다."""
    host, port = _host()
    found = find()
    if host not in ("127.0.0.1", "localhost") or not found:
        return False
    kind, path = found
    if kind == "app" and port == 11434:  # 앱은 기본 포트로만 뜬다
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-g", "-a", str(path)])
        else:
            subprocess.Popen([str(path)], creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    else:
        cli = path if kind == "cli" else (path / "Contents/Resources/ollama" if sys.platform == "darwin" else path.with_name("ollama.exe"))
        kw = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if os.name == "nt" else {"start_new_session": True}
        subprocess.Popen([str(cli), "serve"], env={**os.environ, "OLLAMA_HOST": f"{host}:{port}"},
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)
    for _ in range(int(wait * 2)):
        if local_status()["server"]:
            return True
        time.sleep(0.5)
    return False


def install_mac(on_progress, dest=None):
    """맥: Ollama 앱을 받아 Applications에 푼다(install.sh와 같은 방법). 푼 앱 경로를 돌려준다.
    urllib로 받은 파일에는 '인터넷에서 받음' 표시가 붙지 않으므로 Gatekeeper 경고가 뜨지 않는다."""
    if dest is None:
        dest = Path("/Applications") if os.access("/Applications", os.W_OK) else Path.home() / "Applications"
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    zf = Path(tempfile.mkdtemp()) / "Ollama.zip"
    req = urllib.request.Request(OLLAMA_ZIP, headers={"User-Agent": "KOTEacher"})
    with urllib.request.urlopen(req, timeout=60, context=config.ssl_context()) as r, open(zf, "wb") as f:
        total, done = int(r.headers.get("Content-Length") or 0), 0
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            on_progress("pulling ollama-app", done, total, "ollama-app")
    subprocess.run(["ditto", "-x", "-k", str(zf), str(dest)], check=True)
    zf.unlink()
    return dest / "Ollama.app"


def source(model):
    """모델을 받는 곳 (화면 표시용). 'ghcr.io/…'는 GitHub, 주소 없는 이름은 Ollama 저장소."""
    host = model.split("/")[0] if "/" in model and "." in model.split("/")[0] else ""
    return {"ghcr.io": "GitHub", "hf.co": "Hugging Face", "huggingface.co": "Hugging Face"}.get(host, "Ollama 서버")


class Rate:
    """받기 진행. Ollama는 덩어리 여러 개를 함께 받으며 덩어리마다 진행을 따로 보내므로,
    덩어리별 받은 양을 더해 전체 진행을 내고 최근 WINDOW초 동안 늘어난 양으로 속도와 남은 시간을 낸다."""
    WINDOW = 8

    def __init__(self):
        self.layers, self.hist = {}, []

    def add(self, done, total, digest, now):
        if digest and total:
            self.layers[digest] = (done, total)
        got = sum(d for d, _ in self.layers.values())
        size = sum(t for _, t in self.layers.values())
        self.hist.append((now, got))
        while len(self.hist) > 2 and now - self.hist[1][0] >= self.WINDOW:
            self.hist.pop(0)
        t0, g0 = self.hist[0]
        speed = (got - g0) / (now - t0) if now - t0 >= 1 else 0.0
        return {"done": got, "total": size, "speed": speed,
                "eta": (size - got) / speed if speed > 0 and size > got else None}
