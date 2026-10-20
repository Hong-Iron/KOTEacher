# 유니온 파인드 문서의 그림을 만든다: 15_union-find_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 15_union-find_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "15_union-find"
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


def build(n, unions, by_size):
    """경로 압축 없이 union만 한 뒤, 가장 깊은 칸의 깊이(대표까지 올라가는 횟수)를 잰다."""
    parent, size = list(range(n)), [1] * n

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for a, b in unions:
        a, b = find(a), find(b)
        if a == b:
            continue
        if by_size and size[a] < size[b]:               # 작은 무리를 큰 무리 밑에
            a, b = b, a
        parent[b] = a                                   # 문서와 같이 b의 대표를 a의 대표 밑에
        size[a] += size[b]

    def depth(x):
        d = 0
        while parent[x] != x:
            x, d = parent[x], d + 1
        return d

    return max(depth(x) for x in range(n))


def chain_unions(n):
    """새 칸을 늘 첫째 인자로: union(1, 0), union(2, 1), … 크기를 안 보면 한 줄로 늘어선다."""
    return [(i, i - 1) for i in range(1, n)]


def tournament_unions(n):
    """크기가 같은 무리끼리 짝지어 합치기를 되풀이: 크기로 합쳐도 가장 깊어지는 순서 (n은 2의 거듭제곱)."""
    out, step = [], 1
    while step < n:
        out += [(i, i + step) for i in range(0, n, 2 * step)]
        step *= 2
    return out


KS = list(range(1, 13))
NS = [2 ** k for k in KS]
naive = [build(n, chain_unions(n), by_size=False) for n in NS]
sized_chain = [build(n, chain_unions(n), by_size=True) for n in NS]
sized_worst = [build(n, tournament_unions(n), by_size=True) for n in NS]

fig, ax = plt.subplots(figsize=(6, 3.6))
ax.plot(NS, naive, "o-", color=C[1], lw=1.6, ms=4)
ax.plot(NS, sized_worst, "o-", color=C[0], lw=1.6, ms=4)
ax.text(2 ** 6.6, 400, "크기를 안 보고 합치기\n(같은 순서에서 깊이 $n-1$)", color=C[1], fontsize=10, ha="center")
ax.text(2 ** 8.5, 3.0, r"작은 무리를 큰 무리 밑에 (가장 나쁜 순서에서도 $\log_2 n$)", color=C[0], fontsize=10, ha="center")
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_ylim(0.7, 6000)
ax.set_xlabel("칸 수 $n$")
ax.set_ylabel("가장 깊은 칸의 깊이")
save(fig, 1)

if __name__ == "__main__":
    # 크기를 안 보면 같은 union 순서로 깊이 n − 1, 크기로 합치면 그 순서에서 깊이 1
    assert naive == [n - 1 for n in NS] and sized_chain == [1] * len(NS)
    # 크기로 합칠 때 가장 나쁜 순서에서도 깊이는 정확히 log2 n
    assert sized_worst == KS
    # 무작위 union 300묶음에서도 깊이 <= log2 n
    rng = random.Random(15)
    for _ in range(300):
        n = rng.randint(2, 300)
        us = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(1, 2 * n))]
        assert build(n, us, by_size=True) <= math.log2(n)
    print("ALL CHECKS PASSED")
