"""~/Applications/KOTEacher.app 을 만든다. 저장소의 .venv 파이썬으로 koteacher를 띄우는 작은 묶음이다.

    .venv/bin/python tools/make_app.py
"""
import os
import plistlib
import shutil
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = Path.home() / "Applications" / "KOTEacher.app"
macos = APP / "Contents" / "MacOS"
macos.mkdir(parents=True, exist_ok=True)
(APP / "Contents" / "Resources").mkdir(exist_ok=True)
shutil.copy2(ROOT / "assets" / "KOTEacher.icns", APP / "Contents" / "Resources" / "KOTEacher.icns")

launcher = macos / "koteacher"
launcher.write_text(f"""#!/bin/zsh
cd "{ROOT}"
exec "{ROOT}/.venv/bin/python" -m koteacher >> "$HOME/Library/Logs/KOTEacher.log" 2>&1
""", encoding="utf-8")
launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

with open(APP / "Contents" / "Info.plist", "wb") as f:
    plistlib.dump({
        "CFBundleName": "KOTEacher", "CFBundleDisplayName": "KOTEacher",
        "CFBundleIdentifier": "io.github.hong-iron.koteacher", "CFBundleVersion": "0.2.5",
        "CFBundleShortVersionString": "0.2.5", "CFBundlePackageType": "APPL",
        "CFBundleExecutable": "koteacher", "CFBundleIconFile": "KOTEacher", "LSMinimumSystemVersion": "13.0",
        "NSHighResolutionCapable": True,
    }, f)
os.utime(APP, None)
print(APP)
