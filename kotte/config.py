"""경로와 모델 설정. 환경 변수로 바꿀 수 있다."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT = Path(os.environ.get("KOTTE_VAULT", Path.home() / "Documents/VAULT/공부"))
ALGO = VAULT / "알고리즘"
PRACTICE = ALGO / "4.연습문제"
CONCEPTS = ALGO / "3.개념집"

DATA = Path(os.environ.get("KOTTE_DATA", Path.home() / "Library/Application Support/코테가이드"))
PACKS = DATA / "packs"
DB = DATA / "kotte.db"

OLLAMA = os.environ.get("KOTTE_OLLAMA", "http://127.0.0.1:11434")
MODEL = os.environ.get("KOTTE_MODEL", "gemma4:12b-it-qat")
NUM_CTX = int(os.environ.get("KOTTE_NUM_CTX", "16384"))

# 사용자 코드를 돌리는 파이썬. 앱을 띄운 파이썬과 같은 것을 쓴다.
PYTHON = os.environ.get("KOTTE_PYTHON", "/usr/bin/env python3")


def ensure_dirs():
    PACKS.mkdir(parents=True, exist_ok=True)
