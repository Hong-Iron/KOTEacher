"""경로와 모델 설정. 환경 변수로 바꿀 수 있다."""
import os
import shutil
import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))  # PyInstaller로 묶인 앱
ROOT = Path(sys._MEIPASS) if FROZEN else Path(__file__).resolve().parent.parent

# 문제와 개념 문서. 기본은 저장소의 content/ (볼트에서 tools/sync_content.py로 옮긴 사본).
# 볼트를 바로 읽으려면 KOTEACHER_CONTENT=<볼트>/알고리즘
CONTENT = Path(os.environ.get("KOTEACHER_CONTENT", ROOT / "content"))
PRACTICE = CONTENT / "4.연습문제"
CONCEPTS = CONTENT / "3.개념집"


def _data_dir():
    if os.environ.get("KOTEACHER_DATA"):
        return Path(os.environ["KOTEACHER_DATA"])
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/KOTEacher"
    if os.name == "nt":
        return Path(os.environ.get("APPDATA", Path.home())) / "KOTEacher"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "KOTEacher"


DATA = _data_dir()
# 묶인 앱은 미리 만든 문제 팩을 함께 싣는다
PACKS = ROOT / "packs" if FROZEN and (ROOT / "packs").exists() else DATA / "packs"
DB = DATA / "koteacher.db"

OLLAMA = os.environ.get("KOTEACHER_OLLAMA", "http://127.0.0.1:11434")
# 그림을 읽는 부분(프로젝터, 약 1GB)을 뺀 gemma4:e4b-it-qat. 코치는 그림을 보내지 않으므로 글자 답은 원래 판과 같다
# (온도 0에서 글자까지 같고 견주기 9/12로 같음, eval/results/compare.md). 못 받으면 Ollama 저장소의 원래 판을 받는다(api.pull_model).
E4B_TEXT = "ghcr.io/hong-iron/gemma4-e4b-text:latest"  # GitHub 패키지: 계정 없이 받는다 (tools/push_ghcr.py)
E4B_FALLBACK = "gemma4:e4b-it-qat"
# 앞에서부터 받아져 있는 첫 모델을 쓴다(ollama.status가 고른다). 메모리 8GB 기기는 e4b로 내려간다.
MODELS = [m for m in [os.environ.get("KOTEACHER_MODEL"), "gemma4:12b-it-qat", "gemma4:12b",
                      E4B_TEXT, E4B_FALLBACK, "gemma4:e4b"] if m]
MODEL = MODELS[0]
NUM_CTX = int(os.environ.get("KOTEACHER_NUM_CTX", "8192"))


def ensure_dirs():
    _migrate()
    DATA.mkdir(parents=True, exist_ok=True)
    if not FROZEN:
        PACKS.mkdir(parents=True, exist_ok=True)


def child_cmd(script, *args):
    """학생 코드 검사(harness)와 팩 만들기(capture)를 별도 프로세스로 띄우는 명령.
    묶인 앱에는 python 실행 파일이 없으므로 앱 자신을 '--harness' 같은 인자로 다시 띄운다."""
    if FROZEN:
        return [sys.executable, f"--{script}", *args]
    # -I(격리)는 PYTHONIOENCODING 같은 환경 변수를 무시하므로, 한글 출력을 위해 -X utf8을 직접 준다 (윈도 기본은 cp1252)
    if script == "run":  # 개념 코드 실행
        return [sys.executable, "-I", "-X", "utf8", *args]
    return [sys.executable, "-I", "-X", "utf8", str(ROOT / "koteacher" / f"{script}.py"), *args]


def _migrate():
    """예전 이름(코테가이드)의 기록을 옮긴다."""
    old = DATA.parent / "코테가이드"
    if old.exists() and not DATA.exists():
        shutil.move(str(old), str(DATA))
        if (DATA / "kotte.db").exists():
            (DATA / "kotte.db").rename(DB)


def child_kw():
    """subprocess.run에 함께 넘길 인자. 윈도에서는 검은 콘솔 창을 띄우지 않고, 입출력을 UTF-8로 맞춘다."""
    kw = {"encoding": "utf-8", "errors": "replace"}
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    kw["env"] = env
    if os.name == "nt":
        import subprocess
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kw


# 사용자 설정 (앱 데이터 폴더의 settings.json)
CHOICES = {
    "accurate": {"label": "정확도 우선", "models": ["gemma4:12b-it-qat", "gemma4:12b"], "size": "7.2GB"},
    "fast": {"label": "속도 우선", "models": [E4B_TEXT, E4B_FALLBACK, "gemma4:e4b"], "size": "5.2GB"},
}


def settings():
    import json
    f = DATA / "settings.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(**kw):
    import json
    s = settings() | kw
    DATA.mkdir(parents=True, exist_ok=True)
    f = DATA / "settings.json"
    f.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    try:  # API 키가 들어 있으므로 내 계정만 읽게 한다
        os.chmod(f, 0o600)
    except OSError:
        pass
    return s


# 외부 API. kind는 요청 형식: openai(OpenAI 호환 /chat/completions) 또는 anthropic(/messages)
PROVIDERS = {
    "openai": {"label": "OpenAI", "kind": "openai", "base": "https://api.openai.com/v1",
               "key_url": "https://platform.openai.com/api-keys", "env": "OPENAI_API_KEY"},
    "anthropic": {"label": "Anthropic (Claude)", "kind": "anthropic", "base": "https://api.anthropic.com/v1",
                  "key_url": "https://console.anthropic.com/settings/keys", "env": "ANTHROPIC_API_KEY"},
    "gemini": {"label": "Google Gemini", "kind": "openai", "base": "https://generativelanguage.googleapis.com/v1beta/openai",
               "key_url": "https://aistudio.google.com/apikey", "env": "GEMINI_API_KEY"},
    "openrouter": {"label": "OpenRouter", "kind": "openai", "base": "https://openrouter.ai/api/v1",
                   "key_url": "https://openrouter.ai/keys", "env": "OPENROUTER_API_KEY"},
    "groq": {"label": "Groq", "kind": "openai", "base": "https://api.groq.com/openai/v1",
             "key_url": "https://console.groq.com/keys", "env": "GROQ_API_KEY"},
    "custom": {"label": "OpenAI 호환 서버", "kind": "openai", "base": "", "key_url": "", "env": None},
}


def provider():
    """코치가 쓸 곳: 'ollama'(내 컴퓨터) 또는 PROVIDERS의 이름."""
    p = os.environ.get("KOTEACHER_PROVIDER") or settings().get("provider", "ollama")
    return p if p in PROVIDERS else "ollama"


def api_conf(p=None):
    """외부 API 설정: 주소, 키, 모델. 키는 설정 파일 → 환경 변수 순으로 찾는다."""
    p = p or provider()
    d = PROVIDERS[p]
    saved = (settings().get("api") or {}).get(p, {})
    key = saved.get("key") or (os.environ.get(d["env"]) if d["env"] else None) or ""
    return {"provider": p, "label": d["label"], "kind": d["kind"], "base": (saved.get("base") or d["base"]).rstrip("/"),
            "key": key, "model": saved.get("model") or os.environ.get("KOTEACHER_API_MODEL", ""), "key_url": d["key_url"]}


_SSL = None


def ssl_context():
    """HTTPS 인증서 확인용. python.org 파이썬과 묶인 앱은 맥에서 인증서 묶음이 없어 외부 API가 실패하므로
    맥의 시스템 묶음(/etc/ssl/cert.pem)을 쓴다. 윈도는 파이썬이 시스템 저장소를 읽는다."""
    global _SSL
    if _SSL is None:
        import ssl
        ctx = ssl.create_default_context()
        if not ctx.get_ca_certs() and sys.platform == "darwin" and Path("/etc/ssl/cert.pem").exists():
            ctx.load_verify_locations("/etc/ssl/cert.pem")
        _SSL = ctx
    return _SSL
