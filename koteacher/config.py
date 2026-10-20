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
# 앞에서부터 받아져 있는 첫 모델을 쓴다(ollama.status가 고른다). 메모리 8GB 기기는 e4b로 내려간다.
MODELS = [m for m in [os.environ.get("KOTEACHER_MODEL"), "gemma4:12b-it-qat", "gemma4:12b",
                      "gemma4:e4b-it-qat", "gemma4:e4b"] if m]
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
    if script == "run":  # 개념 코드 실행
        return [sys.executable, "-I", *args]
    return [sys.executable, "-I", str(ROOT / "koteacher" / f"{script}.py"), *args]


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
