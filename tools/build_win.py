"""윈도용 KOTEacher를 만든다 (윈도에서 실행. GitHub Actions의 .github/workflows/build.yml이 돌린다).

    python tools/build_win.py

1. content/로 문제 팩을 만든다
2. PyInstaller로 묶는다 (화면, 문서, 팩, 학생 코드가 쓸 표준 모듈)
3. 묶인 실행 파일이 학생 코드 검사(--harness)와 개념 코드 실행(--run)을 스스로 하는지 점검한다
4. dist/KOTEacher-<버전>-windows-x64.zip 과 Inno Setup 설치 프로그램 dist/KOTEacher-<버전>-Setup.exe 를 만든다
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from build_mac import STDLIB_FOR_USERS, VERSION  # noqa: E402  (같은 모듈 목록과 버전을 쓴다)

STAGE = ROOT / "build" / "stage"
DIST = ROOT / "dist"
ISCC_PATHS = [r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe", r"C:\Program Files\Inno Setup 6\ISCC.exe"]


def run(cmd, **kw):
    print("$", " ".join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True, **kw)


def main():
    os.environ["KOTEACHER_DATA"] = str(ROOT / "build" / "data")
    from koteacher import packs, config
    shutil.rmtree(ROOT / "build", ignore_errors=True)
    print("문제 팩 만들기…", flush=True)
    res = packs.build_all()
    bad = [p["id"] for p in res if not p["ok"]]
    if bad:
        sys.exit(f"팩 실패: {bad} {[p.get('error') for p in res if not p['ok']][:2]}")
    STAGE.mkdir(parents=True)
    shutil.copytree(config.PACKS, STAGE / "packs")

    sep = ";"
    args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed", "--name", "KOTEacher",
            "--icon", str(ROOT / "assets/KOTEacher.ico"),
            "--distpath", str(DIST), "--workpath", str(ROOT / "build/pyi"), "--specpath", str(ROOT / "build"),
            "--add-data", f"{ROOT / 'ui'}{sep}ui",
            "--add-data", f"{ROOT / 'content'}{sep}content",
            "--add-data", f"{STAGE / 'packs'}{sep}packs",
            "--collect-submodules", "koteacher", "--collect-all", "webview"]
    for m in STDLIB_FOR_USERS:
        args += ["--hidden-import", m]
    args.append(str(ROOT / "koteacher_main.py"))
    shutil.rmtree(DIST / "KOTEacher", ignore_errors=True)
    run(args)

    exe = DIST / "KOTEacher" / "KOTEacher.exe"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    req = json.dumps({"code": "import heapq, bisect\nfrom collections import deque, Counter\ndef solution(gems):\n    return [1, 1]\n",
                      "pack": str(STAGE / "packs/pg67258.json"), "repair": True})
    out = subprocess.run([str(exe), "--harness"], input=req, capture_output=True, encoding="utf-8", timeout=120, env=env)
    line = [l for l in out.stdout.splitlines() if l.startswith("{")]
    if not line:
        sys.exit("묶인 앱의 검사 실패:\nstdout=" + out.stdout[-1500:] + "\nstderr=" + out.stderr[-1500:])
    r = json.loads(line[-1])
    print("묶인 앱 검사 점검: 예시", sum(e["ok"] for e in r["examples"]), "/", len(r["examples"]), "· 오류", r.get("load_error"), flush=True)
    if r.get("load_error"):
        sys.exit("학생 코드의 import가 실패했다: " + r["load_error"])
    vf = next((ROOT / "content/3.개념집").glob("*_verify.py"))
    out = subprocess.run([str(exe), "--run", str(vf)], capture_output=True, encoding="utf-8", timeout=180, cwd=vf.parent, env=env)
    print("묶인 앱 개념 코드 점검:", vf.name, out.stdout.strip()[-40:] or out.stderr[-500:], flush=True)
    if "ALL CHECKS PASSED" not in out.stdout:
        sys.exit("묶인 앱에서 개념 코드 실행 실패")

    zip_base = DIST / f"KOTEacher-{VERSION}-windows-x64"
    shutil.make_archive(str(zip_base), "zip", DIST, "KOTEacher")
    print("압축본:", f"{zip_base}.zip", flush=True)

    iscc = next((p for p in ISCC_PATHS if Path(p).exists()), shutil.which("iscc"))
    if not iscc:
        sys.exit("Inno Setup(ISCC.exe)이 없습니다")
    run([iscc, f"/DMyVersion={VERSION}", f"/DSrcDir={DIST / 'KOTEacher'}", f"/DOutDir={DIST}",
         f"/DIconFile={ROOT / 'assets/KOTEacher.ico'}", str(ROOT / "tools/KOTEacher.iss")])
    print("완성:", list(DIST.glob("*.exe")), flush=True)


if __name__ == "__main__":
    main()
