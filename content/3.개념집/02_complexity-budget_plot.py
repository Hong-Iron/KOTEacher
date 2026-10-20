# 시간 복잡도로 방법 고르기 문서의 그림을 만든다: 02_complexity-budget_fig1.svg, 02_complexity-budget_fig2.svg
# 실행: ~/.venvs/vault-plots/bin/python 02_complexity-budget_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "02_complexity-budget"
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



BUDGET = 10**7                                          # 파이썬 1초에 대략 천만 번


def growth(name, n):
    n = np.asarray(n, dtype=float)
    if name == "logn":
        return np.log2(n)
    if name == "n":
        return n
    if name == "nlogn":
        return n * np.log2(n)
    if name == "n2":
        return n ** 2
    if name == "n3":
        return n ** 3
    if name == "2n":
        return 2.0 ** n
    if name == "fact":
        return np.array([math.gamma(v + 1) for v in np.atleast_1d(n)])
    raise ValueError(name)


def crossing(name):
    """growth(name, n) >= BUDGET가 되는 가장 작은 정수 n."""
    hi = 2
    while growth(name, hi) < BUDGET:                    # 넘는 곳을 두 배씩 찾은 뒤
        hi *= 2
    lo = 1
    while lo < hi:                                      # 이분 탐색으로 경계를 찾는다
        mid = (lo + hi) // 2
        if growth(name, mid) >= BUDGET:
            hi = mid
        else:
            lo = mid + 1
    return lo


def append_costs(n):
    """용량을 1에서 시작해 꽉 차면 두 배로 늘리는 배열에 n번 넣을 때, 넣기마다 든 일(옮기기 + 넣기 1)."""
    cap, size, out = 1, 0, []
    for _ in range(n):
        cost = 1
        if size == cap:
            cost += size                                # 새 칸으로 모두 옮긴다
            cap *= 2
        size += 1
        out.append(cost)
    return out


# 그림 1: 복잡도마다 계산 횟수가 n에 따라 늘어나는 모습과 1초 예산
fig, ax = plt.subplots(figsize=(6.2, 4.0))
n_all = np.logspace(0, 7, 400)
curves = [("logn", r"$\log_2 n$"), ("n", "$n$"), ("nlogn", r"$n\log_2 n$"), ("n2", "$n^2$"), ("n3", "$n^3$")]
for i, (key, lab) in enumerate(curves):
    ax.plot(n_all, growth(key, n_all), color=C[i % 5], lw=1.6)
n_small = np.linspace(1, 40, 200)
ax.plot(n_small, growth("2n", n_small), color=C[0], lw=1.6, ls="--")
n_f = np.linspace(1, 16, 200)
ax.plot(n_f, growth("fact", n_f), color=C[1], lw=1.6, ls="--")
ax.axhline(BUDGET, color=INK, lw=1.0, ls=":")
ax.text(60, 3e12, "점선: 파이썬 1초 ≈ $10^7$번", fontsize=10, va="center")
# 예산선을 넘기 시작하는 n을 점 옆에 적는다 (글자 위치는 곡선을 피해 손으로 정했다)
for key, lab, (tx, ty, ha) in [("fact", "$n!$", (10, 4e7, "right")), ("2n", "$2^n$", (30, 1.5e6, "left")),
                               ("n3", "$n^3$", (190, 4e7, "right")), ("n2", "$n^2$", (3800, 1.5e6, "left")),
                               ("nlogn", r"$n\log_2 n$", (4.4e5, 4e7, "right")), ("n", "$n$", (1.3e7, 1e7, "left"))]:
    c = crossing(key)
    ax.plot([c], [BUDGET], "o", color=INK, ms=4, clip_on=False)
    ax.text(tx, ty, f"{lab}: {c:,}", fontsize=9, ha=ha, va="center")
ax.text(3e6, 40, r"$\log_2 n$", fontsize=9, ha="center")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlim(1, 1e7)
ax.set_ylim(1, 1e13)
ax.set_xlabel("입력 크기 $n$")
ax.set_ylabel("계산 횟수")
save(fig, 1)

# 그림 2: 두 배로 늘리는 배열에서 넣기마다 든 일과 그때까지의 평균
N = 64
costs = append_costs(N)
avg = np.cumsum(costs) / np.arange(1, N + 1)
fig, ax = plt.subplots(figsize=(6.2, 3.2))
ax.bar(np.arange(1, N + 1), costs, color=C[0], width=0.8)
ax.plot(np.arange(1, N + 1), avg, color=C[1], lw=2)
ax.axhline(3, color=INK, lw=0.9, ls=":")
ax.text(N + 1.5, 3, "3", fontsize=10, va="center")
ax.text(52, 6.5, "그때까지의 평균", color=C[1], fontsize=10, ha="center")
ax.text(31.5, 31, "33번째: 32개를 옮기고 1개 넣기", fontsize=9, ha="right")
ax.set_xlim(0, N + 4)
ax.set_xlabel("몇 번째 append")
ax.set_ylabel("이번 append에 든 일")
save(fig, 2)

if __name__ == "__main__":
    # 1초 예산(10^7번)을 넘기 시작하는 n: 문서 표의 "파이썬에서 편한 n"보다 조금 크다(두세 배 여유)
    assert crossing("n2") == 3163 and crossing("n3") == 216
    assert crossing("2n") == 24 and crossing("fact") == 11
    assert 5 * 10**5 < crossing("nlogn") < 6 * 10**5
    # 두 배로 늘리기: 몇 번을 넣든 평균 비용은 3 미만, 33번째 넣기는 32개를 옮긴다
    big = append_costs(10**5)
    assert all(s / k < 3 for k, s in enumerate(np.cumsum(big), start=1))
    assert costs[32] == 33 and costs[31] == 1
    print("ALL CHECKS PASSED")
