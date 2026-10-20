# 누적 합과 차분 배열 문서의 그림을 만든다: 19_prefix-sum_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 19_prefix-sum_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "19_prefix-sum"
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



from itertools import accumulate

A = [3, 1, 4, 1, 5, 9]
P = list(accumulate(A, initial=0))                      # [0, 3, 4, 8, 9, 14, 23]
UPDATES = [(1, 3, 2), (2, 5, 5)]                        # a[l..r]에 x 더하기
N = 6
D = [0] * (N + 1)
for l, r, x in UPDATES:
    D[l] += x
    D[r + 1] -= x
RESULT = list(accumulate(D[:N]))

fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 3.1))

# 왼쪽: 누적 합 P는 계단을 쌓아 올린 높이다. 구간 합은 두 높이의 차이다
for i, v in enumerate(A):
    a1.bar(i + 0.5, v, bottom=P[i], width=0.9, color=C[2] if 2 <= i <= 4 else C[0], alpha=0.75)
a1.plot(range(N + 1), P, "o", color=INK, ms=4)
for i, p in enumerate(P):
    a1.text(i - 0.08, p + 0.4, f"P[{i}]={p}", fontsize=8, ha="right", va="bottom")
a1.annotate("", xy=(5.15, P[5]), xytext=(5.15, P[2]), arrowprops=dict(arrowstyle="<->", color=C[1], lw=1.4))
a1.text(5.3, (P[5] + P[2]) / 2, f"{P[5]} - {P[2]}\n= {P[5] - P[2]}", color=C[1], fontsize=9, va="center")
a1.set_xlim(-1.3, 7.2)
a1.set_ylim(0, 27)
a1.set_xticks([i + 0.5 for i in range(N)], [f"a[{i}]" for i in range(N)], fontsize=8)
a1.set_title("누적 합: 구간 합은 높이 차이", fontsize=10)

# 오른쪽: 표시판 D(시작 칸 +x, 끝 다음 칸 −x)를 앞에서부터 더하면 구간마다 더한 값이 나온다
xs = np.arange(N + 1)
a2.bar(xs - 0.25, D, width=0.35, color=C[1], alpha=0.8)
for i, d in enumerate(D):
    if d:
        a2.text(i - 0.25, d + (0.3 if d > 0 else -0.3), f"{d:+d}", color=C[1], fontsize=8, ha="center",
                va="bottom" if d > 0 else "top")
a2.step(np.arange(N + 1), RESULT + [0], where="post", color=C[0], lw=1.8)
a2.axhline(0, color=INK, lw=0.6)
a2.text(3.0, 7.6, "앞에서부터 더한 값", color=C[0], fontsize=9, ha="center")
a2.set_xticks(range(N + 1), [str(i) for i in range(N + 1)], fontsize=8)
a2.set_ylim(-6.5, 9.5)
a2.set_xlabel("칸 번호", fontsize=9)
a2.set_title("차분 배열: 표시 두 개로 구간 더하기", fontsize=10)
fig.tight_layout()
save(fig, 1)

if __name__ == "__main__":
    # 문서 예시: P = [0, 3, 4, 8, 9, 14, 23], P[5] − P[2] = 10 = 4 + 1 + 5
    assert P == [0, 3, 4, 8, 9, 14, 23] and P[5] - P[2] == 10 == sum(A[2:5])
    # 문서 표: D = [0, 2, 5, 0, −2, 0, −5], 앞에서부터 더하면 [0, 2, 7, 7, 5, 5]
    assert D == [0, 2, 5, 0, -2, 0, -5] and RESULT == [0, 2, 7, 7, 5, 5]
    print("ALL CHECKS PASSED")
