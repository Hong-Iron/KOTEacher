"""코테가이드 창을 연다. 맥의 WKWebView로 화면을 그리고, 파이썬 함수를 직접 부른다(서버 없음)."""
import sys

import webview

from . import config, packs
from .api import Api


def _mac_app_name():
    """메뉴 막대와 Dock에 'Python' 대신 앱 이름이 보이게 한다."""
    try:
        from Foundation import NSBundle
        b = NSBundle.mainBundle()
        info = b.localizedInfoDictionary() or b.infoDictionary()
        if info is not None:
            info["CFBundleName"] = "코테가이드"
    except Exception:
        pass


def main():
    _mac_app_name()
    config.ensure_dirs()
    if not any(config.PACKS.glob("*.json")):
        print("문제 팩을 처음 만든다…", file=sys.stderr)
        packs.build_all()
    api = Api()
    index = config.ROOT / "ui" / "index.html"
    win = webview.create_window("코테가이드", url=index.as_uri(), js_api=api, width=1440, height=920,
                                min_size=(900, 600), background_color="#111419")
    api.window = win
    webview.start(debug="--debug" in sys.argv, private_mode=False)


if __name__ == "__main__":
    main()
