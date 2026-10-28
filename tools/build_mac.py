"""맥용 KOTEacher.app과 dmg·pkg를 만든다 (파이썬 없이 열리는 앱).

    .venv/bin/python tools/build_mac.py

1. content/로 문제 팩을 만든다
2. PyInstaller로 앱을 묶는다 (화면, 문서, 팩, 학생 코드가 쓸 표준 모듈 포함)
3. 묶인 앱이 학생 코드 검사(--harness)와 개념 코드 실행(--run)을 스스로 하는지 점검한다
4. dist/KOTEacher-<버전>-<arch>.dmg 를 만든다 (앱 + '설치하고 열기' 스크립트)
5. dist/KOTEacher-<버전>-<arch>.pkg 를 만든다 (설치 프로그램으로 /Applications에 깐다)
"""
import json
import platform
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from koteacher import __version__ as VERSION  # noqa: E402  (버전은 koteacher/__init__.py 한 곳에서)
STAGE = ROOT / "build" / "stage"
DIST = ROOT / "dist"

# 학생 코드가 import할 수 있는 표준 모듈 (코딩 테스트에서 쓰는 것)
STDLIB_FOR_USERS = """heapq bisect collections collections.abc itertools functools math cmath operator string re copy
fractions decimal datetime calendar statistics typing dataclasses array random queue sys io json
enum numbers time textwrap unicodedata pprint""".split()

# dmg 안의 '설치하고 열기' 스크립트. 앱을 /Applications에 복사하고, 인터넷에서 받은 파일에 붙는 표시
# (com.apple.quarantine)를 지운 뒤 연다. 공증받지 않은 앱은 이 표시가 있으면 '손상되었다'며 열리지 않는다.
# 스크립트 자신도 서명이 없어 처음 한 번은 막히지만, 시스템 설정의 '그래도 열기'로 넘어갈 수 있다
# (앱은 임시 서명이라 '손상됨'으로 나오고 그 버튼이 없다).
# KOTEACHER_APP·KOTEACHER_NO_OPEN은 시험용 (다른 곳에 깔기, 열지 않기)
OPEN_SCRIPT = r"""#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="${KOTEACHER_APP:-/Applications/KOTEacher.app}"
wait_key() { echo; read -n 1 -s -r -p "아무 키나 누르면 끝납니다. 이 창은 닫아도 됩니다."; echo; }
echo "KOTEacher 설치하고 열기"
echo
if [ -d "$HERE/KOTEacher.app" ] && [ "$HERE/KOTEacher.app" != "$APP" ]; then
  echo "응용 프로그램 폴더에 복사하는 중…"
  if ! { rm -rf "$APP" && ditto "$HERE/KOTEacher.app" "$APP"; }; then
    echo "복사하지 못했습니다. KOTEacher를 Applications 폴더로 직접 끌어다 놓은 뒤 이 파일을 다시 열어 주세요."
    wait_key; exit 1
  fi
fi
if [ ! -d "$APP" ]; then
  echo "응용 프로그램 폴더에 KOTEacher가 없습니다. KOTEacher를 Applications 폴더로 끌어다 놓은 뒤 이 파일을 다시 열어 주세요."
  wait_key; exit 1
fi
xattr -dr com.apple.quarantine "$APP" 2>/dev/null
if xattr -lr "$APP" 2>/dev/null | grep -q com.apple.quarantine; then
  echo "인터넷에서 받은 표시를 지우지 못했습니다. 터미널에 아래 한 줄을 붙여 넣고 Enter를 눌러 주세요."
  echo "  xattr -dr com.apple.quarantine \"$APP\""
  wait_key; exit 1
fi
echo "준비됐습니다. KOTEacher를 엽니다. 이 창은 닫아도 됩니다."
[ -n "$KOTEACHER_NO_OPEN" ] || open "$APP"
"""

# pkg 설치 뒤: NFD로 담은 한글 파일 이름을 NFC로 되돌린다. $2는 설치한 곳(/Applications).
# 정규화만 다른 이름은 같은 파일로 보이므로 임시 이름을 거쳐 바꾼다. iconv의 UTF-8-MAC은 NFD다
POSTINSTALL = r"""#!/bin/sh
R="$2/KOTEacher.app/Contents/Resources"
[ -d "$R/content" ] || exit 0
cd "$R" || exit 0
find content -depth -print | while IFS= read -r p; do
  b=$(basename "$p")
  n=$(printf '%s' "$b" | iconv -f UTF-8-MAC -t UTF-8)
  if [ "$b" != "$n" ]; then
    d=$(dirname "$p")
    mv "$p" "$d/.kt-nfc-$$" && mv "$d/.kt-nfc-$$" "$d/$n"
  fi
done
exit 0
"""


def run(cmd, **kw):
    print("$", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, **kw)


def main():
    import os
    os.environ["KOTEACHER_DATA"] = str(ROOT / "build" / "data")
    from koteacher import packs, config
    shutil.rmtree(ROOT / "build", ignore_errors=True)
    print("문제 팩 만들기…")
    res = packs.build_all()
    bad = [p["id"] for p in res if not p["ok"]]
    if bad:
        sys.exit(f"팩 실패: {bad}")
    STAGE.mkdir(parents=True)
    shutil.copytree(config.PACKS, STAGE / "packs")

    sep = ":"
    args = [str(ROOT / ".venv/bin/pyinstaller"), "--noconfirm", "--windowed", "--name", "KOTEacher",
            "--icon", str(ROOT / "assets/KOTEacher.icns"),
            "--osx-bundle-identifier", "io.github.hong-iron.koteacher",
            "--distpath", str(DIST), "--workpath", str(ROOT / "build/pyi"), "--specpath", str(ROOT / "build"),
            "--add-data", f"{ROOT / 'ui'}{sep}ui",
            "--add-data", f"{ROOT / 'content'}{sep}content",
            "--add-data", f"{STAGE / 'packs'}{sep}packs",
            "--collect-submodules", "koteacher", "--collect-submodules", "markdown", "--collect-submodules", "pyflakes"]
    for m in STDLIB_FOR_USERS:
        args += ["--hidden-import", m]
    args.append(str(ROOT / "koteacher_main.py"))
    shutil.rmtree(DIST / "KOTEacher.app", ignore_errors=True)
    run(args)

    app = DIST / "KOTEacher.app"
    plist = app / "Contents/Info.plist"
    run(["plutil", "-replace", "CFBundleShortVersionString", "-string", VERSION, str(plist)])
    run(["plutil", "-replace", "CFBundleVersion", "-string", VERSION, str(plist)])
    run(["plutil", "-replace", "CFBundleDisplayName", "-string", "KOTEacher", str(plist)])
    run(["plutil", "-replace", "NSHighResolutionCapable", "-bool", "true", str(plist)])
    # 서명이 없으면 애플 실리콘에서 실행이 막힌다. 개발자 인증서 없이 '임시 서명'만 한다.
    run(["codesign", "--force", "--deep", "--sign", "-", str(app)])

    # 묶인 앱이 학생 코드 검사를 스스로 돌릴 수 있는지 확인
    exe = app / "Contents/MacOS/KOTEacher"
    req = json.dumps({"code": "import heapq, bisect\nfrom collections import deque, Counter\ndef solution(gems):\n    return [1, 1]\n",
                      "pack": str(STAGE / "packs/pg67258.json"), "repair": True})
    out = subprocess.run([str(exe), "--harness"], input=req, capture_output=True, text=True, timeout=60)
    line = [l for l in out.stdout.splitlines() if l.startswith("{")]
    if not line:
        sys.exit("묶인 앱의 검사 실패:\n" + out.stderr[-2000:])
    r = json.loads(line[-1])
    print("묶인 앱 검사 점검: 예시", sum(e["ok"] for e in r["examples"]), "/", len(r["examples"]), "· 오류", r.get("load_error"))
    if r.get("load_error"):
        sys.exit("학생 코드의 import가 실패했다: " + r["load_error"])

    # 묶인 앱이 개념 코드(검증 코드)를 돌릴 수 있는지 확인
    vf = next((ROOT / "content/3.개념집").glob("*_verify.py"))
    out = subprocess.run([str(exe), "--run", str(vf)], capture_output=True, text=True, timeout=120, cwd=vf.parent)
    print("묶인 앱 개념 코드 점검:", vf.name, out.stdout.strip()[-40:] or out.stderr[-300:])
    if "ALL CHECKS PASSED" not in out.stdout:
        sys.exit("묶인 앱에서 개념 코드 실행 실패")

    arch = platform.machine()
    dmg = DIST / f"KOTEacher-{VERSION}-{arch}.dmg"
    dmgsrc = ROOT / "build/dmg"
    shutil.rmtree(dmgsrc, ignore_errors=True)
    dmgsrc.mkdir(parents=True)
    run(["ditto", str(app), str(dmgsrc / "KOTEacher.app")])
    (dmgsrc / "Applications").symlink_to("/Applications")
    script = dmgsrc / "KOTEacher 설치하고 열기.command"
    script.write_text(OPEN_SCRIPT, encoding="utf-8")
    script.chmod(0o755)
    (dmgsrc / "처음 열 때 읽어 주세요.txt").write_text(
        "1. 'KOTEacher 설치하고 열기'를 더블클릭해 주세요. 앱을 Applications 폴더에 복사하고,\n"
        "   인터넷에서 받은 파일에 붙는 표시를 지운 뒤 엽니다.\n"
        "   (이 앱은 Apple 공증을 받지 않아, 그 표시가 있으면 '손상되었기 때문에 열 수 없습니다'가 뜹니다.)\n"
        "2. '…을(를) 열지 않음 · 악성 코드가 없음을 확인할 수 없습니다' 창이 뜨면: 파란 '휴지통으로 이동'이 아니라 '완료'를 누르고,\n"
        "   시스템 설정 → 개인정보 보호 및 보안 → 맨 아래 '그래도 열기'를 누른 뒤 스크립트를 다시 더블클릭해 주세요.\n"
        "   (macOS 15부터는 오른쪽 클릭 → 열기로는 넘어가지 않습니다.)\n"
        "3. 스크립트 대신 직접 하려면: KOTEacher를 Applications 폴더로 끌어다 놓고,\n"
        "   터미널(응용 프로그램 → 유틸리티 → 터미널)에 아래 한 줄을 붙여 넣고 Enter를 누른 뒤 앱을 여세요.\n"
        "     xattr -dr com.apple.quarantine /Applications/KOTEacher.app\n"
        "4. 앱을 열면 코치(AI) 준비 창이 뜨고, 코치 모델(5.2GB)을 바로 받기 시작합니다.\n"
        "   Ollama가 꺼져 있으면 켜고, 없으면 창의 'Ollama 설치하고 모델 받기' 버튼 하나로 설치까지 합니다.\n"
        "   받는 동안에도 문제 풀기, 테스트, 반례 찾기, 개념 문서는 바로 쓸 수 있습니다.\n", encoding="utf-8")
    if dmg.exists():
        dmg.unlink()
    run(["hdiutil", "create", "-volname", "KOTEacher", "-srcfolder", str(dmgsrc), "-ov", "-format", "UDZO", str(dmg)])
    print("완성:", dmg, f"{dmg.stat().st_size / 2**20:.0f}MB")
    make_pkg(app, arch)


def make_pkg(app, arch):
    """pkg: 설치 프로그램이 깐 앱에는 인터넷에서 받은 표시가 붙지 않아, '손상됨'과 터미널 명령이 둘 다 필요 없다.
    pkg 자신은 서명이 없어 처음 한 번 '그래도 열기'가 필요하다. 묶은 앱만 다시 담으려면:
        .venv/bin/python -c "import sys; sys.path.insert(0, 'tools'); import build_mac as b; b.make_pkg(b.DIST / 'KOTEacher.app', 'arm64')"
    """
    pkg = DIST / f"KOTEacher-{VERSION}-{arch}.pkg"
    pkgroot = ROOT / "build/pkgroot"
    shutil.rmtree(pkgroot, ignore_errors=True)
    pkgroot.mkdir(parents=True)
    run(["ditto", str(app), str(pkgroot / "KOTEacher.app")])
    # pkgbuild은 한글 파일 이름이 조합형(NFC)이면 'package.bom을 저장하지 못했다'며 실패하고, 분해형(NFD)만 담는다.
    # 담을 때는 NFD로 바꾸고, 설치가 끝나면 postinstall이 앱이 쓰는 NFC로 되돌린다 (앱은 NFC 이름끼리 견준다)
    for p in sorted(pkgroot.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        nfd = unicodedata.normalize("NFD", p.name)
        if nfd != p.name:
            p.rename(p.with_name(nfd))
    scripts = ROOT / "build/pkgscripts"
    shutil.rmtree(scripts, ignore_errors=True)
    scripts.mkdir(parents=True)
    (scripts / "postinstall").write_text(POSTINSTALL, encoding="utf-8")
    (scripts / "postinstall").chmod(0o755)
    plist = ROOT / "build/component.plist"
    run(["pkgbuild", "--analyze", "--root", str(pkgroot), str(plist)])
    # 기본값(옮길 수 있음)이면, 같은 앱이 다른 곳(예: dist/)에 있을 때 설치 프로그램이 /Applications 대신 그쪽을 덮어쓴다
    run(["plutil", "-replace", "0.BundleIsRelocatable", "-bool", "NO", str(plist)])
    if pkg.exists():
        pkg.unlink()
    run(["pkgbuild", "--root", str(pkgroot), "--component-plist", str(plist), "--scripts", str(scripts),
         "--identifier", "io.github.hong-iron.koteacher", "--version", VERSION, "--install-location", "/Applications", str(pkg)])
    print("완성:", pkg, f"{pkg.stat().st_size / 2**20:.0f}MB")


if __name__ == "__main__":
    main()
