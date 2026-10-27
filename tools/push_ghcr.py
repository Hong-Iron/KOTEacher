"""내 컴퓨터의 Ollama 모델을 GitHub 패키지(ghcr.io)에 올린다. 받는 사람은 계정 없이
`ollama pull ghcr.io/hong-iron/<이름>`으로 받는다 (표준 라이브러리만).

    python3 tools/push_ghcr.py <로컬 모델> <ghcr 이름:태그> [--small]
    예) python3 tools/push_ghcr.py gemma4:e4b-it-qat-text ghcr.io/hong-iron/gemma4-e4b-text:latest

--small: 100MB가 넘는 덩어리(모델 본체)는 빼고 올린다. 받기가 되는지 시험할 때 쓴다.
gh 로그인에 write:packages 권한이 있어야 한다(gh auth refresh -s write:packages).
처음 올린 패키지는 비공개라서, GitHub의 패키지 설정에서 공개로 바꿔야 남이 받을 수 있다.
"""
import base64
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MODELS = Path.home() / ".ollama" / "models"
SMALL = 100 * 2 ** 20
# python.org 파이썬은 인증서 묶음이 없으므로 맥의 것을 쓴다 (koteacher/config.py의 ssl_context와 같은 까닭)
CTX = ssl.create_default_context(cafile="/etc/ssl/cert.pem" if os.path.exists("/etc/ssl/cert.pem") else None)


def local_manifest(name):
    """Ollama가 모델 구성(manifest)을 두는 곳. 새 판(manifests-v2)과 옛 판(manifests)을 모두 찾는다."""
    repo, _, tag = name.partition(":")
    if "/" not in repo:
        repo = "library/" + repo
    for p in (MODELS / "manifests-v2" / "ollama.com" / repo / (tag or "latest"),
              MODELS / "manifests" / "registry.ollama.ai" / repo / (tag or "latest")):
        if p.exists():
            return json.loads(p.read_text())
    sys.exit(f"로컬에 {name} 모델이 없습니다")


def blob(digest):
    return MODELS / "blobs" / digest.replace(":", "-")


class Ghcr:
    def __init__(self, repo):
        self.repo = repo
        self.user = subprocess.run(["gh", "api", "user", "-q", ".login"], capture_output=True, text=True, check=True).stdout.strip()
        self.secret = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
        self.token, self.got = None, 0

    def auth(self):
        """올리기 열쇠. 몇 분이면 만료되므로 4분마다 새로 받는다."""
        if not self.token or time.time() - self.got > 240:
            basic = base64.b64encode(f"{self.user}:{self.secret}".encode()).decode()
            q = urllib.parse.urlencode({"scope": f"repository:{self.repo}:push,pull", "service": "ghcr.io"})
            req = urllib.request.Request(f"https://ghcr.io/token?{q}", headers={"Authorization": f"Basic {basic}"})
            self.token, self.got = json.load(urllib.request.urlopen(req, timeout=30, context=CTX))["token"], time.time()
        return {"Authorization": f"Bearer {self.token}"}

    def call(self, method, url, data=None, headers=None, timeout=60):
        if not url.startswith("https://"):
            url = urllib.parse.urljoin("https://ghcr.io", url)
        req = urllib.request.Request(url, data=data, method=method, headers={**self.auth(), **(headers or {})})
        return urllib.request.urlopen(req, timeout=timeout, context=CTX)

    def has(self, digest):
        try:
            return self.call("HEAD", f"/v2/{self.repo}/blobs/{digest}").status == 200
        except urllib.error.HTTPError:
            return False

    # 한 번에 보내는 양. 6.5GB(12B)를 요청 하나로 보내니 37%에서 GitHub가 연결을 끊었다(2026-10-27)
    CHUNK = 128 * 2 ** 20
    TRIES = 5

    def upload(self, digest, path):
        """덩어리를 CHUNK씩 나눠 올린다. 한 조각이 끊기면 GitHub가 받은 데까지 확인하고 거기서 이어 보낸다."""
        size = path.stat().st_size
        if self.has(digest):
            print(f"  {digest[:19]} 이미 있음")
            return
        loc = self.call("POST", f"/v2/{self.repo}/blobs/uploads/", data=b"").headers["Location"]
        t0, start, fails = time.time(), 0, 0
        with open(path, "rb") as f:
            while start < size:
                f.seek(start)
                body = f.read(self.CHUNK)
                try:
                    r = self.call("PATCH", loc, data=body, timeout=600, headers={
                        "Content-Type": "application/octet-stream", "Content-Range": f"{start}-{start + len(body) - 1}"})
                    loc, start, fails = r.headers["Location"], start + len(body), 0
                except urllib.error.HTTPError as e:
                    # GitHub는 올리던 곳의 진행을 GET으로 알려 주지 않는다(404). 끊긴 조각을 사실은 받았으면
                    # 같은 자리를 다시 보낼 때 416과 함께 받은 데까지(Range: 0-<끝>)를 알려 준다
                    if e.code != 416 or "-" not in (e.headers.get("Range") or ""):
                        raise
                    start = int(e.headers["Range"].rsplit("-", 1)[1]) + 1
                except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                    fails += 1
                    if fails > self.TRIES:
                        raise
                    print(f"\n  끊겼습니다({e}). {5 * fails}초 뒤 같은 자리부터 다시 보냅니다 ({fails}/{self.TRIES})")
                    time.sleep(5 * fails)
                rate = start / max(time.time() - t0, 1e-9) / 2 ** 20
                print(f"\r  {start / size:6.1%} · {rate:.1f}MB/s", end="", flush=True)
        sep = "&" if "?" in loc else "?"
        # 확정할 때 GitHub가 받은 덩어리 전체의 digest를 다시 계산한다. 6.5GB(12B)는 1분을 넘겨 기본 시간 제한에 걸렸다(2026-10-27)
        self.call("PUT", f"{loc}{sep}digest={urllib.parse.quote(digest)}", data=b"", timeout=1800,
                  headers={"Content-Length": "0", "Content-Type": "application/octet-stream"})
        print(f"\r  {digest[:19]} 올림 ({size / 2 ** 20:,.1f}MB, {time.time() - t0:.0f}초)          ")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    local, target = args
    small = "--small" in sys.argv
    target = target.removeprefix("ghcr.io/")
    repo, _, tag = target.partition(":")
    tag = tag or "latest"
    m = local_manifest(local)
    m["layers"] = [{k: v for k, v in l.items() if k != "from"} for l in m["layers"]
                   if not (small and l["size"] > SMALL)]
    g = Ghcr(repo)
    print(f"ghcr.io/{repo}:{tag} 에 올립니다 (덩어리 {len(m['layers']) + 1}개)")
    for d in [m["config"]] + m["layers"]:
        g.upload(d["digest"], blob(d["digest"]))
    body = json.dumps(m, separators=(",", ":")).encode()
    g.call("PUT", f"/v2/{repo}/manifests/{tag}", data=body, headers={"Content-Type": m["mediaType"]})
    print(f"완료: ollama pull ghcr.io/{repo}:{tag}")


if __name__ == "__main__":
    main()
