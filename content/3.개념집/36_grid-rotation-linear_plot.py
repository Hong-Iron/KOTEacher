# 격자 회전 ↔ 선형변환 문서의 그림을 만든다: 36_grid-rotation-linear_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 36_grid-rotation-linear_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "36_grid-rotation-linear"
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



from matplotlib.patches import Rectangle

A = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
FLIP = A[::-1]                                          # 위아래 뒤집기
ROT = [list(r) for r in zip(*A[::-1])]                  # 뒤집은 뒤 전치 = 시계 방향 90°
MARK = {1: C[1], 2: C[0], 3: C[2]}                      # 첫 줄 세 칸을 색으로 따라간다


def draw(ax, g, title, mirror=None):
    n = len(g)
    for r in range(n):
        for c in range(n):
            v = g[r][c]
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor=MARK.get(v, "none"), alpha=0.3 if v in MARK else 1,
                                   edgecolor=INK, lw=0.8))
            ax.text(c + 0.5, r + 0.5, str(v), ha="center", va="center", fontsize=12)
    if mirror == "row":                                 # 가운데 행을 지나는 가로 거울
        ax.plot([-0.2, n + 0.2], [1.5, 1.5], color=C[3], lw=1.6, ls="--")
    if mirror == "diag":                                # 왼쪽 위에서 오른쪽 아래로 가는 대각선 거울
        ax.plot([-0.2, n + 0.2], [-0.2, n + 0.2], color=C[3], lw=1.6, ls="--")
    ax.set_xlim(-0.3, n + 0.3)
    ax.set_ylim(n + 0.3, -0.3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10, color=INK)


fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.6))
draw(axes[0], A, "a\n거울: 가로줄", mirror="row")
draw(axes[1], FLIP, "a[::-1]\n거울: 대각선", mirror="diag")
draw(axes[2], ROT, "zip(*a[::-1])\n= 시계 방향 90°")
for x in [0.355, 0.655]:
    fig.text(x, 0.42, "→", fontsize=18, ha="center", va="center", color=INK)
fig.subplots_adjust(wspace=0.35)
save(fig, 1)

if __name__ == "__main__":
    # 문서 표: 뒤집기 [[7,8,9],[4,5,6],[1,2,3]], 시계 방향 [[7,4,1],[8,5,2],[9,6,3]]
    assert FLIP == [[7, 8, 9], [4, 5, 6], [1, 2, 3]]
    assert ROT == [[7, 4, 1], [8, 5, 2], [9, 6, 3]]
    # 칸 번호 식: (r, c) → (c, n−1−r). 반사 두 행렬의 곱이 회전 행렬 R_{-90°}
    n = 3
    for r in range(n):
        for c in range(n):
            assert ROT[c][n - 1 - r] == A[r][c]
    T = np.array([[0, 1], [1, 0]])
    F = np.array([[-1, 0], [0, 1]])
    assert (T @ F == np.array([[0, 1], [-1, 0]])).all()
    print("ALL CHECKS PASSED")
