# 정렬과 정렬 기준 문서의 그림을 만든다: 05_sorting_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 05_sorting_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "05_sorting"
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


def merge_sort_count(a):
    """병합 정렬을 하며 두 값을 비교한 횟수를 센다."""
    if len(a) <= 1:
        return a, 0
    mid = len(a) // 2
    left, cl = merge_sort_count(a[:mid])
    right, cr = merge_sort_count(a[mid:])
    out, i, j, c = [], 0, 0, cl + cr
    while i < len(left) and j < len(right):
        c += 1
        if left[i] <= right[j]:
            out.append(left[i])
            i += 1
        else:
            out.append(right[j])
            j += 1
    out += left[i:] + right[j:]
    return out, c


def insertion_sort_count(a):
    """삽입 정렬(하나씩 앞으로 끼워 넣기)을 하며 비교한 횟수를 센다."""
    a, c = a[:], 0
    for i in range(1, len(a)):
        x, j = a[i], i - 1
        while j >= 0:
            c += 1
            if a[j] <= x:
                break
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = x
    return a, c


rng = random.Random(5)
NS = [2 ** k for k in range(3, 13)]                     # 8 ~ 4096
merge_c, ins_c = [], []
for n in NS:
    data = [rng.random() for _ in range(n)]
    s1, c1 = merge_sort_count(data)
    s2, c2 = insertion_sort_count(data)
    assert s1 == s2 == sorted(data)
    merge_c.append(c1)
    ins_c.append(c2)
slope_merge = np.polyfit(np.log(NS[-4:]), np.log(merge_c[-4:]), 1)[0]
slope_ins = np.polyfit(np.log(NS[-4:]), np.log(ins_c[-4:]), 1)[0]

fig, ax = plt.subplots(figsize=(6, 3.6))
x = np.array(NS, dtype=float)
ax.plot(x, ins_c, "o-", color=C[1], lw=1.6, ms=4)
ax.plot(x, merge_c, "o-", color=C[0], lw=1.6, ms=4)
ax.plot(x, x * np.log2(x), color=INK, lw=1, ls=":")
ax.text(2 ** 6, 1.5e5, f"하나씩 끼워 넣기\n(기울기 {slope_ins:.2f})", color=C[1], fontsize=10, ha="center")
ax.text(2 ** 9.6, 1.2e3, f"병합 정렬 (기울기 {slope_merge:.2f})", color=C[0], fontsize=10, ha="center")
ax.text(2 ** 11.3, 8e4, r"점선: $n\log_2 n$", fontsize=9, ha="right")
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xlabel("원소 수 $n$ (무작위 실수)")
ax.set_ylabel("비교 횟수")
save(fig, 1)

if __name__ == "__main__":
    # 병합 정렬의 비교 횟수는 n log2 n을 넘지 않고, 삽입 정렬은 평균 약 n^2/4
    assert all(c <= n * math.log2(n) for n, c in zip(NS, merge_c))
    assert abs(ins_c[-1] / (NS[-1] ** 2 / 4) - 1) < 0.1
    # 로그-로그 기울기: 병합 정렬은 1에 가깝고(로그 인자 때문에 조금 크다), 삽입 정렬은 2에 가깝다
    assert 1.0 < slope_merge < 1.2 and 1.9 < slope_ins < 2.1
    print("ALL CHECKS PASSED")
