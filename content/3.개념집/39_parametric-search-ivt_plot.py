# 매개변수 탐색 ↔ 사잇값 정리 문서의 그림을 만든다: 39_parametric-search-ivt_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 39_parametric-search-ivt_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "39_parametric-search-ivt"
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



ROOTS = (0.5, 1.5, 3.3)


def f(x):
    return (x - ROOTS[0]) * (x - ROOTS[1]) * (x - ROOTS[2])


def bisect_trace(a, b, steps):
    """f(a) < 0 <= f(b)를 지키며 중점에서 반씩 줄인 구간들."""
    out = [(a, b)]
    for _ in range(steps):
        p = (a + b) / 2
        if f(p) >= 0:
            b = p
        else:
            a = p
        out.append((a, b))
    return out


STEPS = 6
trace = bisect_trace(0.0, 4.0, STEPS)

fig, (top, bot) = plt.subplots(2, 1, figsize=(6, 4.0), sharex=True, gridspec_kw={"height_ratios": [1.5, 1]})
x = np.linspace(-0.1, 4.1, 400)
top.plot(x, f(x), color=C[0], lw=1.8)
top.axhline(0, color=INK, lw=0.7)
for r in ROOTS:
    top.plot([r], [0], "o", color=C[0], ms=5, mfc="none")
top.text(0.5, 0.9, "가장 작은 근 0.5", fontsize=9, ha="center")
top.text(3.75, -2.5, "이분법이 찾는 근 3.3", fontsize=9, ha="center")
for k in range(5):                                      # 정수 칸의 판정 ok(x) = (f(x) >= 0)
    ok = f(k) >= 0
    top.plot([k], [f(k)], "s", color=C[2] if ok else C[1], ms=6)
top.text(4.05, f(4), "참", color=C[2], fontsize=9, va="center")
top.text(0.08, f(0), "거짓", color=C[1], fontsize=9, va="center")
top.set_ylim(-3.2, 7)
top.set_ylabel("$f(x)$")
for k, (a, b) in enumerate(trace):
    bot.plot([a, b], [k, k], color=C[3], lw=3, solid_capstyle="butt")
    bot.text(-0.15, k, f"{k}", fontsize=8, ha="right", va="center")
bot.axvline(ROOTS[2], color=C[0], lw=0.8, ls=":")
bot.set_ylim(STEPS + 0.6, -0.6)
bot.set_yticks([])
bot.spines["left"].set_visible(False)
bot.set_xlabel("$x$")
bot.set_title("반씩 줄인 구간 (위에서부터 0, 1, 2, … 번째)", fontsize=9, loc="left")
fig.tight_layout()
save(fig, 1)

if __name__ == "__main__":
    # 문서 표: 정수 0~4의 판정 줄 = 거짓, 참, 거짓, 거짓, 참. f(0) < 0 < f(4)
    assert [f(k) >= 0 for k in range(5)] == [False, True, False, False, True]
    # 이분법 구간: [0,4] → [2,4] → [3,4] → [3,3.5] → [3.25,3.5] → …, 3.3으로 모인다
    assert trace[:5] == [(0, 4), (2, 4), (3, 4), (3, 3.5), (3.25, 3.5)]
    a, b = bisect_trace(0.0, 4.0, 60)[-1]
    assert abs(a - 3.3) < 1e-12 and abs(b - 3.3) < 1e-12
    print("ALL CHECKS PASSED")
