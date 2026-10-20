# 계산 기하 기초 문서의 그림을 만든다: 35_geometry-ccw_fig1.svg
# 실행: ~/.venvs/vault-plots/bin/python 35_geometry-ccw_plot.py  (matplotlib, numpy 필요)
import math
import os

import matplotlib
matplotlib.use("svg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "35_geometry-ccw"
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



from matplotlib.patches import Arc, Polygon


def cross(o, p, q):
    return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])


def tri_area(a, b, c):
    """신발끈 공식과 다른 길: 세 변 길이로 헤론 공식."""
    la, lb, lc = math.dist(b, c), math.dist(a, c), math.dist(a, b)
    s = (la + lb + lc) / 2
    return math.sqrt(s * (s - la) * (s - lb) * (s - lc))


O, P, Q = (0, 0), (4, 1), (1, 3)
P1, P2, Q1, Q2 = (0, 0), (4, 2), (1, 3), (3, -1)        # 엇갈리는 두 선분 (그림 오른쪽)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.8, 3.2))

# 왼쪽: O → P → Q는 왼쪽으로 꺾고, 외적 11은 삼각형 넓이 5.5의 두 배
a1.add_patch(Polygon([O, P, Q], closed=True, color=C[0], alpha=0.15))
for tgt, col in [(P, C[0]), (Q, C[1])]:
    a1.annotate("", xy=tgt, xytext=O, arrowprops=dict(arrowstyle="-|>", color=col, lw=1.6))
a1.add_patch(Arc(O, 2.2, 2.2, theta1=math.degrees(math.atan2(1, 4)), theta2=math.degrees(math.atan2(3, 1)),
                 color=C[3], lw=1.4))
a1.annotate("", xy=(0.38, 1.04), xytext=(0.6, 0.95), arrowprops=dict(arrowstyle="-|>", color=C[3], lw=1.2))
for name, pt, off in [("O(0, 0)", O, (-0.15, -0.45)), ("P(4, 1)", P, (0.1, -0.4)), ("Q(1, 3)", Q, (0.12, 0.1))]:
    a1.plot(*pt, "o", color=INK, ms=4)
    a1.text(pt[0] + off[0], pt[1] + off[1], name, fontsize=9)
a1.text(1.75, 1.45, "넓이 5.5", color=C[0], fontsize=9, ha="center")
a1.text(1.15, 0.55, "반시계", color=C[3], fontsize=8, ha="center")
a1.text(2.0, 3.6, "cross(O, P, Q) = 4×3 - 1×1 = 11", fontsize=9, ha="center")
a1.set_xlim(-0.8, 5.0)
a1.set_ylim(-0.8, 4.0)
a1.set_aspect("equal")
a1.set_xticks([])
a1.set_yticks([])
for side in ["left", "bottom"]:
    a1.spines[side].set_visible(False)

# 오른쪽: 두 선분이 엇갈리려면 각 선분의 끝점이 상대 직선의 양쪽에 하나씩 있어야 한다
t = np.linspace(-1.5, 2.5, 2)
for (u, v), col in [((P1, P2), C[0]), ((Q1, Q2), C[1])]:
    dx, dy = v[0] - u[0], v[1] - u[1]
    a2.plot(u[0] + t * dx, u[1] + t * dy, color=col, lw=0.8, ls=":")
    a2.plot([u[0], v[0]], [u[1], v[1]], color=col, lw=2.2)
for name, pt, col, line, off in [("p₁", P1, C[0], (Q1, Q2), (-0.2, -0.55)), ("p₂", P2, C[0], (Q1, Q2), (0.15, -0.1)),
                                 ("q₁", Q1, C[1], (P1, P2), (0.15, 0.05)), ("q₂", Q2, C[1], (P1, P2), (0.15, -0.2))]:
    sign = "+" if cross(line[0], line[1], pt) > 0 else "-"
    a2.plot(*pt, "o", color=col, ms=4)
    a2.text(pt[0] + off[0], pt[1] + off[1], f"{name} ({sign})", fontsize=9, color=col)
a2.text(1.0, -1.7, "괄호: 상대 직선의 왼쪽 +, 오른쪽 -", fontsize=8, ha="center")
a2.set_xlim(-1.2, 5.0)
a2.set_ylim(-1.8, 4.0)
a2.set_aspect("equal")
a2.set_xticks([])
a2.set_yticks([])
for side in ["left", "bottom"]:
    a2.spines[side].set_visible(False)
fig.tight_layout()
save(fig, 1)

if __name__ == "__main__":
    # 문서 예시: cross(O, P, Q) = 11 > 0(왼쪽), 순서를 바꾸면 −11, 넓이는 11 / 2
    assert cross(O, P, Q) == 11 and cross(O, Q, P) == -11
    assert abs(tri_area(O, P, Q) - 5.5) < 1e-9
    # 오른쪽 그림: 네 부호가 둘씩 엇갈려 두 선분이 엇갈린다
    d = [cross(P1, P2, Q1), cross(P1, P2, Q2), cross(Q1, Q2, P1), cross(Q1, Q2, P2)]
    assert d == [10, -10, -10, 10] and d[0] * d[1] < 0 and d[2] * d[3] < 0
    print("ALL CHECKS PASSED")
