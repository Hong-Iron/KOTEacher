"""KOTEacher 창을 연다. 맥의 WKWebView로 화면을 그리고, 파이썬 함수를 직접 부른다(서버 없음)."""
import os
import signal
import sys
import threading

import webview

from . import config, ollama, packs
from .api import Api


def _mac_app_name():
    """메뉴 막대와 Dock에 'Python' 대신 앱 이름이 보이게 한다."""
    try:
        from Foundation import NSBundle
        b = NSBundle.mainBundle()
        info = b.localizedInfoDictionary() or b.infoDictionary()
        if info is not None:
            info["CFBundleName"] = "KOTEacher"
    except Exception:
        pass


def main():
    _mac_app_name()
    config.ensure_dirs()
    if not any(config.PACKS.glob("*.json")):
        print("문제 팩을 처음 만든다…", file=sys.stderr)
        packs.build_all()
    api = Api()
    # 켤 때: 모델이 이미 올라와 있으면 그대로 쓰고, 없으면 뒤에서 미리 불러온다.
    # 끌 때: 이 앱이 불러온 경우에만 내린다 (다른 프로그램이 쓰던 모델은 건드리지 않는다).
    owned = {"model": False}

    def preload():
        st = ollama.status()
        if st["model"] and not st["loaded"]:
            owned["model"] = True
            try:
                ollama.load()
            except Exception:
                pass

    threading.Thread(target=preload, daemon=True).start()
    index = config.ROOT / "ui" / "index.html"
    win = webview.create_window("KOTEacher", url=index.as_uri(), js_api=api, width=1440, height=920,
                                min_size=(900, 600), background_color="#111419")
    api.window = win

    def on_closed():
        if owned["model"]:
            ollama.unload()

    win.events.closed += on_closed
    # 종료 신호(로그아웃, kill)도 창 닫기와 같게. 맥의 창 이벤트 루프가 주 스레드를 쥐고 있어
    # 파이썬 신호 처리기가 돌 틈이 없으므로, 신호를 파일 기술자로 받아 다른 스레드에서 처리한다.
    if hasattr(signal, "SIGTERM") and os.name != "nt":
        r, w = os.pipe()
        os.set_blocking(w, False)
        signal.set_wakeup_fd(w)
        signal.signal(signal.SIGTERM, lambda *_: None)

        def watch():
            if os.read(r, 1):
                win.destroy()

        threading.Thread(target=watch, daemon=True).start()
    webview.start(debug="--debug" in sys.argv, private_mode=False)
    if owned["model"]:  # 창 이벤트를 못 받고 끝나도 한 번 더
        ollama.unload()


if __name__ == "__main__":
    main()
