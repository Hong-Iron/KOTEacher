# 투 포인터와 슬라이딩 윈도 문서의 그림을 만든다: 18_two-pointers_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 18_two-pointers_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "18_two-pointers"
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

A = [1, 3, 4, 6, 8, 11]
TARGET = 10


def two_pointer_path(a, target):
    """양 끝에서 좁혀 오며 들른 (L, R) 칸 번호. 찾으면 그 칸에서 멈춘다."""
    L, R, path = 0, len(a) - 1, []
    while L < R:
        path.append((L, R))
        s = a[L] + a[R]
        if s == target:
            break
        if s > target:
            R -= 1
        else:
            L += 1
    return path


path = two_pointer_path(A, TARGET)
n = len(A)

# 그림 1: 두 수의 합을 표로 펴 놓고, 두 손가락이 지나간 길
fig, ax = plt.subplots(figsize=(5.2, 4.4))
for i in range(n):
    for j in range(n):
        if j <= i:
            continue
        s = A[i] + A[j]
        face = C[2] if s == TARGET else (C[1] if s > TARGET else C[0])
        ax.add_patch(Rectangle((j, i), 1, 1, facecolor=face, alpha=0.18, edgecolor=INK, lw=0.5))
        ax.text(j + 0.5, i + 0.5, str(s), ha="center", va="center", fontsize=10)
for k, (l, r) in enumerate(path):                      # 들른 칸: 굵은 테두리와 순서 번호
    ax.add_patch(Rectangle((r + 0.06, l + 0.06), 0.88, 0.88, fill=False, edgecolor=C[3], lw=2.2))
    ax.text(r + 0.14, l + 0.12, str(k + 1), color=C[3], fontsize=8, ha="left", va="top")
ax.set_xlim(0, n)
ax.set_ylim(n, 0)
ax.set_xticks([j + 0.5 for j in range(n)], [str(v) for v in A])
ax.set_yticks([i + 0.5 for i in range(n)], [str(v) for v in A])
ax.xaxis.tick_top()
ax.xaxis.set_label_position("top")
ax.set_xlabel("R이 가리키는 수")
ax.set_ylabel("L이 가리키는 수")
ax.tick_params(length=0)
for side in ["left", "top", "bottom", "right"]:
    ax.spines[side].set_visible(False)
for k, (lab, col) in enumerate([("주황 칸: 합이 10보다 크다", C[1]), ("파랑 칸: 합이 10보다 작다", C[0]),
                                ("초록 칸: 합이 10", C[2]), ("보라 테두리: 들른 순서", C[3])]):
    ax.text(0.1, 3.4 + 0.45 * k, lab, color=col, fontsize=9, va="top")
ax.set_aspect("equal")
save(fig, 1)

if __name__ == "__main__":
    # 문서 표와 같은 순서: (1,11) → (1,8) → (3,8) → (3,6) → (4,6)
    assert [(A[l], A[r]) for l, r in path] == [(1, 11), (1, 8), (3, 8), (3, 6), (4, 6)]
    # 표는 위쪽이 작고 오른쪽이 크다: 정렬되어 있어 행마다 오른쪽으로, 열마다 아래로 합이 커진다
    for i in range(n):
        for j in range(i + 1, n - 1):
            assert A[i] + A[j] <= A[i] + A[j + 1]
    # 모든 쌍 15칸 중 5칸만 들렀다
    assert n * (n - 1) // 2 == 15 and len(path) == 5
    print("ALL CHECKS PASSED")
