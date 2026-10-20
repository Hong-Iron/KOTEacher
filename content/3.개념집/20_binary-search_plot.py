# 이분 탐색 문서의 그림을 만든다: 20_binary-search_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 20_binary-search_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "20_binary-search"
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



def lower_bound_steps(n, pos):
    """0..n-1이 정렬된 리스트에서 답이 pos(0..n)인 x를 찾을 때 while을 도는 횟수."""
    lo, hi, steps = 0, n, 0
    while lo < hi:
        mid = (lo + hi) // 2
        steps += 1
        if mid < pos:                                   # a[mid] < x
            lo = mid + 1
        else:
            hi = mid
    return steps


def worst_steps(n):
    """가장 오래 걸리는 경우의 횟수: 범위 n + 1가지를 반씩 줄이므로 ⌈log2(n + 1)⌉."""
    return math.ceil(math.log2(n + 1))


NS = np.unique(np.logspace(0, 6, 600).astype(int))
fig, ax = plt.subplots(figsize=(6, 3.6))
ax.plot(NS, NS, color=C[1], lw=1.6)
ax.step(NS, [worst_steps(n) for n in NS], where="post", color=C[0], lw=1.6)
ax.plot([10**6], [10**6], "o", color=C[1], ms=4)
ax.plot([10**6], [worst_steps(10**6)], "o", color=C[0], ms=4)
ax.text(10**5.8, 3e6, "앞에서부터 하나씩: 100만 번", color=C[1], fontsize=10, ha="right", va="center")
ax.set_ylim(0.6, 1e7)
ax.text(10**5.9, 45, f"이분 탐색: {worst_steps(10**6)}번", color=C[0], fontsize=10, ha="right")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("정렬된 원소 수 $n$")
ax.set_ylabel("가장 나쁠 때 비교 횟수")
save(fig, 1)

if __name__ == "__main__":
    # 모든 답 위치를 다 넣어 본 최댓값이 ⌈log2(n + 1)⌉과 같다 (n = 1 ~ 2048)
    for n in range(1, 2049):
        assert max(lower_bound_steps(n, p) for p in range(n + 1)) == worst_steps(n)
    # 문서 예시: 8칸에서 7(번호 3) 찾기는 3번, 100만 개에서는 20번
    assert lower_bound_steps(8, 3) == 3 and worst_steps(10**6) == 20
    print("ALL CHECKS PASSED")
