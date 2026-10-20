"""맥용 KOTEacher.app과 dmg를 만든다 (파이썬 없이 열리는 앱).

    .venv/bin/python tools/build_mac.py

1. content/로 문제 팩을 만든다
2. PyInstaller로 앱을 묶는다 (화면, 문서, 팩, 학생 코드가 쓸 표준 모듈 포함)
3. 앱을 띄워 스스로 점검한다 (--selftest)
4. dist/KOTEacher-<버전>-<arch>.dmg 를 만든다
"""
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
VERSION = "0.1.0"
STAGE = ROOT / "build" / "stage"
DIST = ROOT / "dist"

# 학생 코드가 import할 수 있는 표준 모듈 (코딩 테스트에서 쓰는 것)
STDLIB_FOR_USERS = """heapq bisect collections collections.abc itertools functools math cmath operator string re copy
fractions decimal datetime calendar statistics typing dataclasses array random queue sys io json
enum numbers time textwrap unicodedata pprint""".split()


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
            "--collect-submodules", "koteacher"]
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

    arch = platform.machine()
    dmg = DIST / f"KOTEacher-{VERSION}-{arch}.dmg"
    dmgsrc = ROOT / "build/dmg"
    shutil.rmtree(dmgsrc, ignore_errors=True)
    dmgsrc.mkdir(parents=True)
    run(["ditto", str(app), str(dmgsrc / "KOTEacher.app")])
    (dmgsrc / "Applications").symlink_to("/Applications")
    (dmgsrc / "처음 열 때 읽어 주세요.txt").write_text(
        "1. KOTEacher를 Applications 폴더로 끌어다 놓아 주세요.\n"
        "2. 처음 열 때 '확인되지 않은 개발자' 경고가 뜨면: Finder에서 KOTEacher를 오른쪽 클릭 → 열기 → 열기를 누르면 됩니다.\n"
        "   (또는 시스템 설정 → 개인정보 보호 및 보안 → '그래도 열기')\n"
        "3. 앱이 코치(AI) 준비를 안내합니다: Ollama 설치(ollama.com/download) → 앱 안에서 모델 받기.\n"
        "   AI 없이도 문제 풀기, 테스트, 반례 찾기, 개념 문서는 바로 쓸 수 있습니다.\n", encoding="utf-8")
    if dmg.exists():
        dmg.unlink()
    run(["hdiutil", "create", "-volname", "KOTEacher", "-srcfolder", str(dmgsrc), "-ov", "-format", "UDZO", str(dmg)])
    print("완성:", dmg, f"{dmg.stat().st_size / 2**20:.0f}MB")


if __name__ == "__main__":
    main()
