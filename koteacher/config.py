"""경로와 모델 설정. 환경 변수로 바꿀 수 있다."""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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
PACKS = DATA / "packs"
DB = DATA / "koteacher.db"

OLLAMA = os.environ.get("KOTEACHER_OLLAMA", "http://127.0.0.1:11434")
# 앞에서부터 받아져 있는 첫 모델을 쓴다(ollama.status가 고른다). 메모리 8GB 기기는 e4b로 내려간다.
MODELS = [m for m in [os.environ.get("KOTEACHER_MODEL"), "gemma4:12b-it-qat", "gemma4:12b",
                      "gemma4:e4b-it-qat", "gemma4:e4b"] if m]
MODEL = MODELS[0]
NUM_CTX = int(os.environ.get("KOTEACHER_NUM_CTX", "8192"))


def ensure_dirs():
    _migrate()
    PACKS.mkdir(parents=True, exist_ok=True)


def _migrate():
    """예전 이름(코테가이드)의 기록을 옮긴다."""
    old = DATA.parent / "코테가이드"
    if old.exists() and not DATA.exists():
        shutil.move(str(old), str(DATA))
        if (DATA / "kotte.db").exists():
            (DATA / "kotte.db").rename(DB)
