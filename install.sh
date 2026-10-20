#!/usr/bin/env bash
# KOTEacher 한 번에 설치 (맥, Linux)
#
#   curl -fsSL https://raw.githubusercontent.com/Hong-Iron/KOTEacher/main/install.sh | bash
#
# 하는 일: 파이썬 확인 → 앱 내려받기 → 패키지 설치 → 문제 팩 → Ollama 설치 → gemma4 모델 받기 → 앱 아이콘 만들기
# 바꿀 수 있는 것 (환경 변수):
#   KOTEACHER_DIR=설치 폴더 (기본 ~/KOTEacher)
#   KOTEACHER_MODEL=gemma4:e4b-it-qat  (모델을 직접 고를 때)
#   KOTEACHER_SKIP_MODEL=1  (모델 받기를 건너뛸 때)
set -euo pipefail

REPO="https://github.com/Hong-Iron/KOTEacher.git"
DIR="${KOTEACHER_DIR:-$HOME/KOTEacher}"
OS="$(uname -s)"

say()  { printf '\n\033[1;34m▶ %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
fail() { printf '\n\033[31m✗ %s\033[0m\n' "$*"; exit 1; }

# ---------------------------------------------------------------- 1. 파이썬
say "파이썬 확인"
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then PY="$(command -v "$c")"; break; fi
done
if [ -z "$PY" ]; then
  if [ "$OS" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    say "Homebrew로 파이썬을 설치합니다"; brew install python; PY="$(command -v python3)"
  else
    fail "파이썬 3.10 이상이 필요합니다. https://www.python.org/downloads/ 에서 설치한 뒤 다시 실행해 주세요."
  fi
fi
ok "$("$PY" --version) ($PY)"

# ---------------------------------------------------------------- 2. 앱 내려받기
say "KOTEacher 내려받기 → $DIR"
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull --ff-only && ok "최신으로 업데이트했습니다"
else
  command -v git >/dev/null 2>&1 || fail "git이 필요합니다. 맥은 'xcode-select --install', Linux는 패키지 관리자로 설치해 주세요."
  git clone --depth 1 "$REPO" "$DIR" && ok "받았습니다"
fi
cd "$DIR"

# ---------------------------------------------------------------- 3. 패키지
say "패키지 설치 (가상환경 .venv)"
if [ "$OS" = "Linux" ]; then
  echo "  Linux에서는 창을 띄우는 데 GTK WebKit이 필요합니다. 없으면 먼저 설치해 주세요:"
  echo "    Ubuntu/Debian: sudo apt install python3-venv python3-gi gir1.2-webkit2-4.1"
  echo "    Arch: sudo pacman -S python-gobject webkit2gtk-4.1"
fi
"$PY" -m venv .venv $( [ "$OS" = "Linux" ] && echo --system-site-packages )
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt
ok "pywebview, markdown 설치했습니다"

# ---------------------------------------------------------------- 4. 문제 팩
say "문제 팩 만들기 (약 20초)"
.venv/bin/python tools/build_packs.py | head -2

# ---------------------------------------------------------------- 5. Ollama
say "Ollama (내 컴퓨터에서 도는 AI) 확인"
if ! command -v ollama >/dev/null 2>&1 && [ ! -d /Applications/Ollama.app ]; then
  if [ "$OS" = "Darwin" ]; then
    TMP="$(mktemp -d)"
    echo "  ollama.com에서 Ollama 앱을 받습니다"
    curl -fL --progress-bar -o "$TMP/Ollama.zip" https://ollama.com/download/Ollama-darwin.zip
    ditto -x -k "$TMP/Ollama.zip" /Applications
    rm -rf "$TMP"
  else
    curl -fsSL https://ollama.com/install.sh | sh
  fi
fi
if [ "$OS" = "Darwin" ] && [ -d /Applications/Ollama.app ]; then open -g -a Ollama || true; fi
for i in $(seq 1 30); do curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1 && break; sleep 1; done
curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1 && ok "Ollama가 켜져 있습니다" || echo "  Ollama가 아직 켜지지 않았습니다. Ollama를 실행한 뒤 앱에서 모델을 받으면 됩니다."

# ---------------------------------------------------------------- 6. 모델
if [ "${KOTEACHER_SKIP_MODEL:-}" != "1" ] && curl -fsS http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
  MODEL="${KOTEACHER_MODEL:-$(.venv/bin/python -c 'from koteacher import ollama; print(ollama.recommend()["model"])')}"
  say "코치 모델 받기: $MODEL (메모리에 맞춰 골랐습니다)"
  OLLAMA_BIN="$(command -v ollama || echo /Applications/Ollama.app/Contents/Resources/ollama)"
  "$OLLAMA_BIN" pull "$MODEL" && ok "모델을 받았습니다"
fi

# ---------------------------------------------------------------- 7. 앱 아이콘
say "앱 아이콘 만들기"
if [ "$OS" = "Darwin" ]; then
  .venv/bin/python tools/make_app.py >/dev/null && ok "~/Applications/KOTEacher.app (Launchpad, Spotlight에서 KOTEacher로 찾을 수 있습니다)"
else
  mkdir -p "$HOME/.local/share/applications"
  cat > "$HOME/.local/share/applications/koteacher.desktop" <<EOF
[Desktop Entry]
Name=KOTEacher
Comment=코딩 테스트 연습과 AI 코치
Exec=sh -c 'cd "$DIR" && .venv/bin/python -m koteacher'
Icon=$DIR/assets/icon-256.png
Terminal=false
Type=Application
Categories=Education;Development;
EOF
  ok "앱 메뉴에 KOTEacher를 넣었습니다"
fi

say "설치가 끝났습니다"
echo "  실행: KOTEacher 앱을 누르거나, 터미널에서  cd \"$DIR\" && .venv/bin/python -m koteacher"
echo "  업데이트: 이 설치 명령을 한 번 더 실행하면 됩니다."
