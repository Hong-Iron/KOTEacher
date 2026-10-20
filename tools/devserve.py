"""개발용: 화면을 브라우저에서 확인할 때 쓰는 다리. 앱은 이걸 쓰지 않는다.

    .venv/bin/python tools/devserve.py   →  http://127.0.0.1:8766/
127.0.0.1에만 묶는다. Api 함수를 POST /api/<이름>으로, 코치 이벤트를 GET /events로 준다.
"""
import json
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from kotte.api import Api  # noqa: E402

api = Api()
events, lock = [], threading.Lock()


class Win:
    def evaluate_js(self, js):
        # "window.KG && KG.on(<ev>, <data>)"에서 인자만 뽑는다
        inner = js[js.index("KG.on(") + 6:-1]
        ev, data = inner.split(", ", 1)
        with lock:
            events.append([json.loads(ev), json.loads(data)])


api.window = Win()


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT / "ui"), **k)

    def log_message(self, *a):
        pass

    def do_POST(self):
        if self.path == "/events":
            with lock:
                out = list(events)
                events.clear()
            return self._json(out)
        name = self.path.split("/api/")[1]
        args = json.loads(self.rfile.read(int(self.headers["Content-Length"])) or b"[]")
        try:
            res = getattr(api, name)(*args)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())
            return
        self._json(res)

    def _json(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8766
    print(f"http://127.0.0.1:{port}/")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
