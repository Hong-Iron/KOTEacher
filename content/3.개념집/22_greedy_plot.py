# 그리디 문서의 그림을 만든다: 22_greedy_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 22_greedy_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "22_greedy"
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



from itertools import combinations

MEETINGS = {"A": (1, 4), "B": (3, 5), "C": (0, 6), "D": (5, 7), "E": (3, 8), "F": (5, 9), "G": (6, 10), "H": (8, 11)}


def greedy(meetings):
    """끝나는 시각 순으로 보며, 앞 회의가 끝난 뒤 시작하는 회의를 넣는다."""
    chosen, end = [], float("-inf")
    for name, (s, e) in sorted(meetings.items(), key=lambda kv: kv[1][1]):
        if s >= end:
            chosen.append(name)
            end = e
    return chosen


def brute_max(meetings):
    items = list(meetings.values())
    for r in range(len(items), 0, -1):
        for combo in combinations(items, r):
            iv = sorted(combo)
            if all(iv[i][1] <= iv[i + 1][0] for i in range(len(iv) - 1)):
                return r
    return 0


chosen = greedy(MEETINGS)
order = sorted(MEETINGS, key=lambda k: MEETINGS[k][1])  # 끝나는 시각 순으로 위에서 아래로

fig, ax = plt.subplots(figsize=(6, 3.4))
for row, name in enumerate(order):
    s, e = MEETINGS[name]
    pick = name in chosen
    ax.barh(row, e - s, left=s, height=0.6, color=C[0] if pick else INK, alpha=0.85 if pick else 0.25)
    ax.text(s - 0.15, row, name, ha="right", va="center", fontsize=10, color=C[0] if pick else INK)
for name in chosen[:-1]:
    e = MEETINGS[name][1]
    ax.axvline(e, color=C[1], lw=1, ls=":")
    ax.text(e, -0.9, f"{e}에 끝남", color=C[1], fontsize=9, ha="center")
ax.set_ylim(len(order) - 0.4, -1.3)
ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_xticks(range(0, 12))
ax.set_xlim(-0.8, 11.5)
ax.set_xlabel("시각 (위에서부터 끝나는 시각 순)")
save(fig, 1)

if __name__ == "__main__":
    # 문서 예시: 그리디는 A, D, H를 고르고, 모든 조합을 봐도 3개가 최대
    assert chosen == ["A", "D", "H"] and brute_max(MEETINGS) == 3
    assert order == ["A", "B", "C", "D", "E", "F", "G", "H"]
    print("ALL CHECKS PASSED")
