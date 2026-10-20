# 매개변수 탐색 문서의 그림을 만든다: 21_parametric-search_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 21_parametric-search_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "21_parametric-search"
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



LOGS = [8, 5, 11]
NEED = 5


def pieces(L):
    return sum(x // L for x in LOGS)


def max_true_trace(lo, hi, ok):
    """문서의 max_true 틀. 물어본 mid를 차례로 모은다."""
    asked = []
    while lo < hi:
        mid = (lo + hi + 1) // 2
        asked.append(mid)
        if ok(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo, asked


ans, asked = max_true_trace(1, 11, lambda L: pieces(L) >= NEED)
Ls = list(range(1, 12))
cnt = [pieces(L) for L in Ls]

fig, ax = plt.subplots(figsize=(6, 3.4))
ax.axvspan(0.5, ans + 0.5, color=C[2], alpha=0.10)
ax.axvspan(ans + 0.5, 11.5, color=C[1], alpha=0.08)
ax.bar(Ls, cnt, width=0.6, color=[C[2] if c >= NEED else C[1] for c in cnt], alpha=0.8)
for L, c in zip(Ls, cnt):
    ax.text(L, c + 0.4, str(c), ha="center", fontsize=9)
ax.axhline(NEED, color=INK, lw=0.9, ls=":")
ax.text(11.6, NEED, "5개", fontsize=9, va="center")
for k, L in enumerate(asked):
    ax.text(L, 15, f"{k + 1}", color=C[3], fontsize=9, ha="center", va="center",
            bbox=dict(boxstyle="circle,pad=0.2", fc="none", ec=C[3], lw=1))
ax.text(6.6, 15, "← 이분 탐색이 물은 순서", color=C[3], fontsize=9, ha="left", va="center")
ax.text(2.5, 21, "된다", color=C[2], fontsize=10, ha="center")
ax.text(8, 21, "안 된다", color=C[1], fontsize=10, ha="center")
ax.set_xticks(Ls)
ax.set_xlim(0.5, 11.5)
ax.set_ylim(0, 26)
ax.set_xlabel("자르는 길이 L")
ax.set_ylabel("토막 수")
save(fig, 1)

if __name__ == "__main__":
    # 문서 표: L = 1..6에서 토막 24, 11, 6, 5, 4, 2. 답 4. 물어본 순서 6, 3, 4, 5
    assert cnt[:6] == [24, 11, 6, 5, 4, 2]
    assert ans == 4 and asked == [6, 3, 4, 5]
    # 토막 수는 L이 커지면 늘지 않는다(단조성)
    assert all(a >= b for a, b in zip(cnt, cnt[1:]))
    print("ALL CHECKS PASSED")
