"""~/Applications/코테가이드.app 을 만든다. 저장소의 .venv 파이썬으로 kotte를 띄우는 작은 묶음이다.

    .venv/bin/python tools/make_app.py
"""
import os
import plistlib
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = Path.home() / "Applications" / "코테가이드.app"
macos = APP / "Contents" / "MacOS"
macos.mkdir(parents=True, exist_ok=True)
(APP / "Contents" / "Resources").mkdir(exist_ok=True)

launcher = macos / "kotte"
launcher.write_text(f"""#!/bin/zsh
cd "{ROOT}"
exec "{ROOT}/.venv/bin/python" -m kotte >> "$HOME/Library/Logs/코테가이드.log" 2>&1
""", encoding="utf-8")
launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

with open(APP / "Contents" / "Info.plist", "wb") as f:
    plistlib.dump({
        "CFBundleName": "코테가이드", "CFBundleDisplayName": "코테가이드",
        "CFBundleIdentifier": "io.github.hong-iron.kotte-guide", "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0", "CFBundlePackageType": "APPL",
        "CFBundleExecutable": "kotte", "LSMinimumSystemVersion": "13.0", "NSHighResolutionCapable": True,
    }, f)
os.utime(APP, None)
print(APP)
