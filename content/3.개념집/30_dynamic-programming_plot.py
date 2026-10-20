# 동적 계획법 문서의 그림을 만든다: 30_dynamic-programming_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 30_dynamic-programming_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "30_dynamic-programming"
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



def naive_calls(n):
    """f(n) = f(n-1) + f(n-2)를 그대로 재귀로 구할 때 함수를 부르는 횟수. 횟수 자체도 같은 점화식을 따른다."""
    calls = [1, 1]                                      # f(0), f(1)은 한 번 부르고 끝난다
    for k in range(2, n + 1):
        calls.append(1 + calls[k - 1] + calls[k - 2])
    return calls[n]


def memo_calls(n):
    """구한 값을 딕셔너리에 적어 두는 재귀에서 함수를 부르는 횟수."""
    memo, count = {}, 0

    def f(k):
        nonlocal count
        count += 1
        if k in memo:
            return memo[k]
        memo[k] = k if k < 2 else f(k - 1) + f(k - 2)
        return memo[k]

    f(n)
    return count


def naive_calls_direct(n):
    count = 0

    def f(k):
        nonlocal count
        count += 1
        return k if k < 2 else f(k - 1) + f(k - 2)

    f(n)
    return count


NS = list(range(1, 31))
naive = [naive_calls(n) for n in NS]
memo = [memo_calls(n) for n in NS]

fig, ax = plt.subplots(figsize=(6, 3.5))
ax.plot(NS, naive, "o-", color=C[1], lw=1.6, ms=3)
ax.plot(NS, memo, "o-", color=C[0], lw=1.6, ms=3)
ax.text(29.5, naive[-1], f"그대로 재귀: {naive[-1]:,}번", color=C[1], fontsize=10, ha="right", va="bottom")
ax.text(29.5, memo[-1] * 2.5, f"표에 적어 두기: {memo[-1]}번", color=C[0], fontsize=10, ha="right", va="bottom")
ax.set_yscale("log")
ax.set_xlabel("구하는 피보나치 수의 번호 $n$")
ax.set_ylabel("함수를 부른 횟수")
save(fig, 1)

if __name__ == "__main__":
    # 문서 예시: f(30)을 그대로 재귀로 구하면 2,692,537번, 표에 적으면 59번
    assert naive[-1] == 2_692_537 and memo[-1] == 59
    # 점화식으로 센 횟수가 실제로 센 횟수와 같다 (n <= 20)
    assert all(naive_calls(n) == naive_calls_direct(n) for n in range(0, 21))
    # 표에 적으면 2n − 1번 (n >= 1)
    assert memo == [2 * n - 1 for n in NS]
    print("ALL CHECKS PASSED")
