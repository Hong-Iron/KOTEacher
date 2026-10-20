# 딕셔너리와 집합 문서의 그림을 만든다: 04_hash-dict-set_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 04_hash-dict-set_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "04_hash-dict-set"
INK = "#888888"                                         # 밝은 테마와 어두운 테마 모두에서 보이는 회색
C = ["#3b82c4", "#d9622b", "#3a9a5b", "#9b59b6", "#c49a1b"]
_fonts = {f.name for f in font_manager.fontManager.ttflist}
FONT = next((n for n in ["Apple SD Gothic Neo", "NanumGothic", "Noto Sans CJK KR"] if n in _fonts), "DejaVu Sans")
plt.rcParams.update({
    "font.family": FONT, "mathtext.fontset": "dejavusans",
    "font.size": 11, "axes.unicode_minus": False, "svg.fonttype": "path", "svg.hashsalt": PREFIX,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "text.color": INK, "legend.frameon": False,
    "axes.facecolor": "none", "figure.facecolor": "none", "savefig.transparent": True,
    "axes.spines.top": False, "axes.spines.right": False,
})


def save(fig, k):
    fig.savefig(os.path.join(HERE, f"{PREFIX}_fig{k}.svg"), bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)



import random


class TinyDict:
    """04_hash-dict-set_impl.py의 TinyDict와 같은 규칙: 칸마다 목록을 매달고, 키 수가 칸 수를 넘으면 칸을 두 배로."""

    def __init__(self):
        self.m, self.n = 8, 0
        self.slots = [[] for _ in range(self.m)]

    def put(self, key):
        slot = self.slots[hash(key) % self.m]
        if key in slot:
            return
        slot.append(key)
        self.n += 1
        if self.n > self.m:
            items = [k for s in self.slots for k in s]
            self.m *= 2
            self.slots = [[] for _ in range(self.m)]
            for k in items:
                self.slots[hash(k) % self.m].append(k)

    def avg_compare(self):
        """들어 있는 키를 하나씩 찾을 때 평균 비교 횟수(칸 목록에서 몇 번째인가)."""
        total = sum(i + 1 for s in self.slots for i in range(len(s)))
        return total / self.n


N = 2000
rng = random.Random(1)
keys = rng.sample(range(10**9), N)                      # 정수 키: hash가 실행마다 같다
d = TinyDict()
load, hash_cmp = [], []
for k in keys:
    d.put(k)
    load.append(d.n / d.m)
    hash_cmp.append(d.avg_compare())
ns = np.arange(1, N + 1)
list_cmp = (ns + 1) / 2                                 # 리스트: 평균 (n + 1)/2번 비교

fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 3.0))
a1.plot(ns, load, color=C[0], lw=1.3)
a1.axhline(1, color=INK, lw=0.8, ls=":")
a1.set_ylim(0, 1.15)
a1.set_xlabel("넣은 키 수 $n$")
a1.set_title("칸 하나당 키 수 (n / 칸 수)", fontsize=10)
a2.plot(ns, list_cmp, color=C[1], lw=1.6)
a2.plot(ns, hash_cmp, color=C[0], lw=1.6)
a2.text(1300, 70, "리스트에서 찾기", color=C[1], fontsize=10, ha="center")
a2.text(1300, 2.6, "딕셔너리에서 찾기", color=C[0], fontsize=10, ha="center")
a2.set_yscale("log")
a2.set_ylim(0.8, 2000)
a2.set_xlabel("넣은 키 수 $n$")
a2.set_title("키 하나 찾을 때 평균 비교 횟수", fontsize=10)
fig.tight_layout()
save(fig, 1)

if __name__ == "__main__":
    # 칸이 차면 두 배로 늘리므로 칸 하나당 키 수는 늘 1 이하이고, 늘린 직후에는 1/2 남짓으로 떨어진다
    assert max(load) <= 1 and min(load[8:]) > 0.5
    # 키 2000개에서 딕셔너리 찾기는 평균 2번 미만, 리스트는 1000.5번
    assert max(hash_cmp) < 2 and list_cmp[-1] == 1000.5
    print("ALL CHECKS PASSED")
