"""IU와 콘의 보드게임 (프로그래머스 1841) 풀이와 검증."""
import random
import time
from functools import cmp_to_key
from itertools import product


def cross(o, p, q):
    """o에서 p, q를 볼 때의 외적. 양수면 p → q가 반시계 방향."""
    return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])


def angle_rank(o, first, last, pins):
    """o에서 first 쪽부터 last 쪽으로 돌며 핀에 1, 2, …를 매긴다."""
    turn = 1 if cross(o, first, last) > 0 else -1
    order = sorted(range(len(pins)), key=cmp_to_key(lambda i, j: -turn * (1 if cross(o, pins[i], pins[j]) > 0 else -1)))
    rank = [0] * len(pins)
    for r, i in enumerate(order, 1):
        rank[i] = r
    return rank


def solution(n, triangle, v, table=None):
    A, B, C = map(tuple, triangle)
    pins = [tuple(p) for p in v]
    al = angle_rank(A, B, C, pins)             # A에서 AB 쪽부터: AB 주머니 핀이 CA 주머니 핀보다 먼저
    be = angle_rank(B, A, C, pins)             # B에서 BA 쪽부터: AB 주머니 핀이 BC 주머니 핀보다 먼저
    ga = angle_rank(C, B, A, pins)             # C에서 CB 쪽부터: BC 주머니 핀이 CA 주머니 핀보다 먼저
    by_al, by_be, by_ga = [0] * (n + 1), [0] * (n + 1), [0] * (n + 1)
    for i in range(n):
        by_al[al[i]], by_be[be[i]], by_ga[ga[i]] = i, i, i

    # L[a][b]: α ≤ a, β > b인 핀의 γ 최댓값 (없으면 0)
    # R[a][b]: α > a, β ≤ b인 핀의 γ 최솟값 (없으면 n + 1)
    grid = [[0] * (n + 2) for _ in range(n + 2)]
    for i in range(n):
        grid[al[i]][be[i]] = ga[i]
    L = [[0] * (n + 1) for _ in range(n + 1)]
    for a in range(1, n + 1):
        row, prev, best = grid[a], L[a - 1], 0
        cur = L[a]
        for b in range(n, -1, -1):             # β > b 쪽을 뒤에서부터 모은다
            cur[b] = max(prev[b], best)
            best = max(best, row[b])
    R = [[n + 1] * (n + 1) for _ in range(n + 2)]
    for a in range(n - 1, -1, -1):
        row, nxt, best = grid[a + 1], R[a + 1], n + 1
        cur = R[a]
        for b in range(n + 1):                 # β ≤ b 쪽을 앞에서부터 모은다
            if b >= 1 and row[b]:
                best = min(best, row[b])
            cur[b] = min(nxt[b], best)
    # ok[b][c]: c = 0이거나 γ 순위 c인 핀의 β가 b보다 크다. 그 누적 합
    okp = []
    for b in range(n + 1):
        pre = [1]                              # c = 0
        for c in range(1, n + 1):
            pre.append(pre[-1] + (be[by_ga[c]] > b))
        okp.append(pre)

    total = 0
    for a in range(n + 1):
        for b in range(n + 1):
            if (a == 0) != (b == 0):
                continue
            if a and (be[by_al[a]] > b or al[by_be[b]] > a):
                continue                       # 경계 핀이 AB 주머니에 들지 못한다
            lo, hi = L[a][b], R[a][b] - 1      # c는 lo ~ hi
            if lo <= hi:
                pre = okp[b]
                got = pre[hi] - (pre[lo - 1] if lo else 0)
                total += got
                if table is not None and got:
                    table[(a, b)] = (lo, hi, got)
    return total


def hull_chain(P, Q, pts):
    """밑변 PQ 위에서 pts를 감싸는 볼록 껍질의 사슬 P → … → Q. P를 축으로 각도 순서로 훑는다."""
    side = 1 if cross(P, Q, pts[0]) > 0 else -1
    order = sorted(pts, key=cmp_to_key(lambda p, q: -1 if side * cross(P, p, q) < 0 else 1))
    chain = [P]
    for p in order + [Q]:
        while len(chain) >= 2 and side * cross(chain[-2], chain[-1], p) >= 0:
            chain.pop()
        chain.append(p)
    return chain


def inside_convex(poly, p):
    """볼록 다각형 poly 안이나 변 위에 p가 있는가."""
    signs = {(cross(poly[i], poly[(i + 1) % len(poly)], p) > 0) - (cross(poly[i], poly[(i + 1) % len(poly)], p) < 0)
             for i in range(len(poly))}
    return not (1 in signs and -1 in signs)


def crosses(p1, p2, q1, q2):
    if {p1, p2} & {q1, q2}:
        return False
    d1, d2 = cross(p1, p2, q1), cross(p1, p2, q2)
    d3, d4 = cross(q1, q2, p1), cross(q1, q2, p2)
    return d1 * d2 < 0 and d3 * d4 < 0


def by_coloring(n, triangle, v):
    """핀마다 세 주머니 중 하나를 모두 골라, 주머니를 그려 겹치는지 직접 본다(작은 입력만)."""
    A, B, C = map(tuple, triangle)
    pins = [tuple(p) for p in v]
    sides = [(A, B), (B, C), (C, A)]
    count = 0
    for colors in product(range(3), repeat=n):
        chains, polys = [], []
        for s, (P, Q) in enumerate(sides):
            grp = [pins[i] for i in range(n) if colors[i] == s]
            ch = hull_chain(P, Q, grp) if grp else [P, Q]
            chains.append(ch)
            polys.append(ch)
        ok = True
        for i in range(n):                     # 다른 주머니 안에 든 핀이 없어야 한다
            for s in range(3):
                if s != colors[i] and len(polys[s]) > 2 and inside_convex(polys[s], pins[i]):
                    ok = False
        for s in range(3):                     # 고무줄끼리 엇갈리면 안 된다
            for t in range(s + 1, 3):
                for e in zip(chains[s], chains[s][1:]):
                    for f in zip(chains[t], chains[t][1:]):
                        if crosses(e[0], e[1], f[0], f[1]):
                            ok = False
        count += ok
    return count


def random_case(n, rng, span, check=True):
    """넓은 삼각형과 그 안의 핀 n개. 세 점이 한 줄에 서지 않게 하고, 막히면 처음부터 다시 만든다."""
    while True:
        tri = [(rng.randint(-span, span), rng.randint(-span, span)) for _ in range(3)]
        if abs(cross(*tri)) < span * span:     # 너무 좁은 삼각형은 버린다
            continue
        pts, tries = [], 0
        while len(pts) < n and tries < 2000:
            tries += 1
            p = (rng.randint(-span, span), rng.randint(-span, span))
            a, b, c = (cross(tri[0], tri[1], p), cross(tri[1], tri[2], p), cross(tri[2], tri[0], p))
            if not ((a > 0 and b > 0 and c > 0) or (a < 0 and b < 0 and c < 0)):
                continue
            allp = tri + pts
            if check and any(cross(allp[i], allp[j], p) == 0 for i in range(len(allp)) for j in range(i + 1, len(allp))):
                continue                       # 세 점이 한 줄에 서지 않게
            pts.append(p)
        if len(pts) == n:
            return [list(t) for t in tri], [list(p) for p in pts]


if __name__ == "__main__":
    ex1 = (2, [[0, 8], [-4, 0], [4, 0]], [[-1, 3], [1, 4]])
    ex2 = (10, [[-13, 40], [-27, -48], [31, 6]],
           [[2, 21], [15, -1], [6, -13], [-20, -27], [5, 9], [5, 11], [-18, -26], [-15, 19], [7, 4], [-5, -18]])
    assert solution(*ex1) == 6 == by_coloring(*ex1)
    tb = {}
    solution(*ex1, tb)
    assert tb == {(0, 0): (0, 2, 3), (1, 1): (0, 2, 2), (2, 2): (0, 2, 1)}   # 6단계 표
    A, B, C = (0, 8), (-4, 0), (4, 0)
    D, E = (-1, 3), (1, 4)
    assert angle_rank(A, B, C, [D, E]) == angle_rank(B, A, C, [D, E]) == angle_rank(C, B, A, [D, E]) == [1, 2]
    assert solution(*ex2) == 73 == by_coloring(*ex2)
    assert solution(0, [[0, 0], [4, 0], [0, 4]], []) == 1
    rng = random.Random(1841)
    for _ in range(400):
        n = rng.randint(0, 6)
        tri, pins = random_case(n, rng, 30)
        assert solution(n, tri, pins) == by_coloring(n, tri, pins), (tri, pins)
    # 핀 500개
    tri, pins = random_case(500, rng, 10 ** 8, check=False)   # 좌표가 넓어 세 점이 한 줄일 일이 거의 없다
    t0 = time.perf_counter()
    solution(500, tri, pins)
    t = time.perf_counter() - t0
    assert t < 20, t
    print(f"핀 500개: {t:.2f}s")
    print("ALL CHECKS PASSED")
