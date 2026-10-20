"""41.위상 정렬 ↔ 동적 계획법의 계산 순서: 문서의 표, 수, 주장을 확인한다.

화살표 규칙: (a, b)는 "b를 구할 때 a를 읽는다", 곧 a가 먼저다.
구간 DP의 칸 번호는 31.구간 DP처럼 1부터 센다.
"""
import heapq
import itertools
import random
import sys
from collections import defaultdict

INF = float("inf")
rng = random.Random(41)


# ---------------------------------------------------------------- 공용 도구
def is_linear_extension(order, nodes, arrows):
    """order가 nodes를 한 번씩 담고, 모든 화살표 (a, b)에서 a가 b보다 앞인가."""
    if len(order) != len(nodes) or set(order) != set(nodes):
        return False
    pos = {v: i for i, v in enumerate(order)}
    return all(pos[a] < pos[b] for a, b in arrows if a in pos and b in pos)


def linear_extensions(nodes, arrows):
    return [p for p in itertools.permutations(nodes) if is_linear_extension(p, nodes, arrows)]


def kahn(nodes, arrows):
    """칸 알고리즘. 고리가 있으면 꺼내지 못한 점이 남는다."""
    indeg = {v: 0 for v in nodes}
    out = defaultdict(list)
    for a, b in arrows:
        out[a].append(b)
        indeg[b] += 1
    ready = [v for v in nodes if indeg[v] == 0]
    order = []
    while ready:
        v = ready.pop()
        order.append(v)
        for w in out[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                ready.append(w)
    return order, [v for v in nodes if v not in set(order)]


def has_cycle_three_colors(nodes, arrows):
    out = defaultdict(list)
    for a, b in arrows:
        out[a].append(b)
    color = {v: 0 for v in nodes}

    def go(v):
        color[v] = 1
        for w in out[v]:
            if color[w] == 1 or (color[w] == 0 and go(w)):
                return True
        color[v] = 2
        return False

    return any(color[v] == 0 and go(v) for v in nodes)


def minimal_elements(nodes, arrows):
    has_in = {b for a, b in arrows}
    return {v for v in nodes if v not in has_in}


def down_set(goal, arrows):
    """goal보다 앞서야 하는 원소 전체(goal 포함): 화살표를 거슬러 닿는 점."""
    reads = defaultdict(list)
    for a, b in arrows:
        reads[b].append(a)
    seen, stack = {goal}, [goal]
    while stack:
        v = stack.pop()
        for u in reads[v]:
            if u not in seen:
                seen.add(u)
                stack.append(u)
    return seen


def memo_run(goal, reads_fn, combine):
    """위에서부터 기억하기. 칸을 끝낸 순서를 함께 돌려준다."""
    memo, finish = {}, []

    def f(s):
        if s in memo:
            return memo[s]
        vals = [f(t) for t in reads_fn(s)]
        memo[s] = combine(s, vals)
        finish.append(s)
        return memo[s]

    f(goal)
    return memo, finish


def random_dag(n, p):
    hidden = list(range(n))
    rng.shuffle(hidden)
    arrows = [(hidden[i], hidden[j]) for i in range(n) for j in range(i + 1, n) if rng.random() < p]
    return list(range(n)), arrows


# ------------------------------------------------- A. 동전 DP (30의 예시)
def coin_arrows(X, coins):
    return [(x - c, x) for x in range(X + 1) for c in coins if c <= x]


def coin_combine(x, vals):
    if x == 0:
        return 0
    return min(v + 1 for v in vals) if vals else INF


coins, X = [1, 3, 4], 6
nodes = list(range(X + 1))
arr = coin_arrows(X, coins)
memo, finish = memo_run(X, lambda x: [x - c for c in coins if c <= x], coin_combine)
assert [memo[x] for x in range(X + 1)] == [0, 1, 2, 1, 1, 2, 2]          # 30의 표
assert sorted(a for a, b in arr if b == 6) == [2, 3, 5]                     # dp[6]은 dp[5], dp[3], dp[2]를 읽는다
assert minimal_elements(nodes, arr) == {0}
les = linear_extensions(nodes, arr)
assert les == [tuple(range(7))]                                            # 1원이 있으면 순서가 한 가지뿐
assert finish == list(range(7)) and is_linear_extension(finish, nodes, arr)
assert not is_linear_extension(finish[::-1], nodes, arr)
for cs in ([1, 2], [1, 5, 6, 9], [1, 3]):                                 # 1원이 들어가면 늘 한 가지
    nd = list(range(8))
    assert len(linear_extensions(nd, coin_arrows(7, cs))) == 1

# 동전 3원, 4원: dp[0], dp[1], dp[2]가 모두 극소 원소, 6원이면 네 칸만 계산
c34 = [3, 4]
arr34 = coin_arrows(6, c34)
assert minimal_elements(list(range(7)), arr34) == {0, 1, 2}
m34, f34 = memo_run(6, lambda x: [x - c for c in c34 if c <= x], coin_combine)
assert set(m34) == {0, 2, 3, 6} == down_set(6, arr34)
assert f34 == [0, 3, 2, 6] and is_linear_extension(f34, list(m34), arr34)
assert m34 == {0: 0, 3: 1, 2: INF, 6: 2}
assert not ({1, 4, 5} & set(m34))                                           # 6원과 상관없는 칸

# ------------------------------- B. 먼저 비교해 보기: 구간 DP 세 칸과 11의 그래프
def interval_cells(k):
    return [(i, j) for i in range(1, k + 1) for j in range(i, k + 1)]


def interval_arrows(k):
    arrows = set()
    for i, j in interval_cells(k):
        for m in range(i, j):
            arrows.add(((i, m), (i, j)))
            arrows.add(((m + 1, j), (i, j)))
    return sorted(arrows)


cells3, arr3 = interval_cells(3), interval_arrows(3)
A, B, C, AB, BC, ABC = (1, 1), (2, 2), (3, 3), (1, 2), (2, 3), (1, 3)
assert sorted(a for a, b in arr3 if b == ABC) == sorted([A, BC, AB, C])   # [A,B,C]가 읽는 칸
assert minimal_elements(cells3, arr3) == {A, B, C}
assert is_linear_extension([A, B, C, AB, BC, ABC], cells3, arr3)            # 길이 순
assert is_linear_extension([C, B, BC, A, AB, ABC], cells3, arr3)            # 시작점 큰 것부터
i_asc = sorted(cells3)                                                     # 시작점 작은 것부터
assert i_asc[:2] == [A, AB] and not is_linear_extension(i_asc, cells3, arr3)
assert (B, AB) in arr3                                                     # [A,B]는 [B]를 읽는다
assert len(linear_extensions(cells3, arr3)) == 16

F, E, L, T, D, I = "함수", "지수", "로그", "삼각", "미분", "적분"
nodes11 = [F, E, L, T, D, I]
arr11 = [(F, E), (E, L), (L, D), (F, T), (T, D), (D, I)]
assert len(linear_extensions(nodes11, arr11)) == 3
assert is_linear_extension([F, E, L, T, D, I], nodes11, arr11)
assert is_linear_extension([F, T, E, L, D, I], nodes11, arr11)
assert not is_linear_extension([F, L, E, T, D, I], nodes11, arr11)        # 로그를 지수보다 앞에
assert minimal_elements(nodes11, arr11) == {F}


# ------------------------------------ C. 구간 DP: 여러 순서, 확인 문제 C1
class Unfilled(Exception):
    pass


def chain_by_order(d, order_key):
    k = len(d) - 1
    dp = {}
    for i, j in sorted(interval_cells(k), key=order_key):
        if i == j:
            dp[i, j] = 0
            continue
        best = INF
        for m in range(i, j):
            if (i, m) not in dp or (m + 1, j) not in dp:
                raise Unfilled
            best = min(best, dp[i, m] + dp[m + 1, j] + d[i - 1] * d[m] * d[j])
        dp[i, j] = best
    return dp[1, k]


def chain_brute(d, i, j):
    if i == j:
        return 0
    return min(chain_brute(d, i, m) + chain_brute(d, m + 1, j) + d[i - 1] * d[m] * d[j] for m in range(i, j))


ORDERS_OK = {
    "길이 순": lambda c: (c[1] - c[0], c[0]),
    "시작점 큰 것부터": lambda c: (-c[0], c[1]),
    "끝점 작은 것부터, 시작점 큰 것부터": lambda c: (c[1], -c[0]),
}
ORDERS_BAD = {
    "시작점 작은 것부터": lambda c: (c[0], c[1]),
    "끝점 작은 것부터, 시작점 작은 것부터": lambda c: (c[1], c[0]),
}
assert chain_by_order([10, 30, 5, 60], ORDERS_OK["길이 순"]) == 4500     # 31의 예시
for k in range(2, 9):
    cells, arrows = interval_cells(k), interval_arrows(k)
    for key in ORDERS_OK.values():
        assert is_linear_extension(sorted(cells, key=key), cells, arrows)
    for key in ORDERS_BAD.values():
        assert not is_linear_extension(sorted(cells, key=key), cells, arrows)
# C1의 예: 끝점·시작점 모두 작은 것부터면 dp[1][2]가 dp[2][2]보다 먼저 온다
bad = sorted(interval_cells(3), key=ORDERS_BAD["끝점 작은 것부터, 시작점 작은 것부터"])
assert bad.index((1, 2)) < bad.index((2, 2))
trials = 0
for _ in range(1500):
    k = rng.randint(2, 7)
    d = [rng.randint(1, 40) for _ in range(k + 1)]
    want = chain_brute(d, 1, k)
    for key in ORDERS_OK.values():
        assert chain_by_order(d, key) == want
    for key in ORDERS_BAD.values():
        try:
            chain_by_order(d, key)
            raise AssertionError("잘못된 순서가 빈 칸을 읽지 않았다")
        except Unfilled:
            pass
    trials += 1
assert trials == 1500


# ------------- D. 기억하기의 끝나는 순서 vs 25의 '끝나는 순서를 거꾸로' (확인 문제 C3)
def dfs_finish_forward(nodes, arrows):
    """화살표를 '먼저 → 나중' 방향으로 따라가는 DFS의 끝나는 순서(25)."""
    out = defaultdict(list)
    for a, b in arrows:
        out[a].append(b)
    seen, fin = set(), []

    def go(v):
        seen.add(v)
        for w in out[v]:
            if w not in seen:
                go(w)
        fin.append(v)

    for v in nodes:
        if v not in seen:
            go(v)
    return fin


cnt_memo = 0
for _ in range(2000):
    n = rng.randint(2, 14)
    nodes_r, arrows_r = random_dag(n, rng.random() * 0.6)
    reads = defaultdict(list)
    for a, b in arrows_r:
        reads[b].append(a)
    for v in reads:
        rng.shuffle(reads[v])
    goal = rng.randrange(n)
    memo_r, fin_r = memo_run(goal, lambda s: reads[s], lambda s, vals: 1 + sum(vals))
    sub = down_set(goal, arrows_r)
    assert set(memo_r) == sub                                     # 목표 아래쪽만 계산
    sub_arrows = [(a, b) for a, b in arrows_r if a in sub and b in sub]
    assert is_linear_extension(fin_r, list(sub), sub_arrows)      # 끝나는 순서 그대로가 선형 확장
    if sub_arrows:
        assert not is_linear_extension(fin_r[::-1], list(sub), sub_arrows)
    fwd = dfs_finish_forward(nodes_r, arrows_r)
    assert is_linear_extension(fwd[::-1], nodes_r, arrows_r)     # 25: 거꾸로 하면 선형 확장
    if arrows_r:
        assert not is_linear_extension(fwd, nodes_r, arrows_r)
    cnt_memo += 1
assert cnt_memo == 2000


# ------------------------- E. 방문 순서를 거꾸로: 나무에서만 (확인 문제 C2)
def reversed_preorder(root, children):
    order, stack, seen = [], [root], {root}
    while stack:
        v = stack.pop()
        order.append(v)
        for c in children[v]:
            if c not in seen:
                seen.add(c)
                stack.append(c)
    return order[::-1]


for _ in range(1500):
    n = rng.randint(1, 15)
    parent = {v: rng.randrange(v) for v in range(1, n)}
    children = defaultdict(list)
    for v, p in parent.items():
        children[p].append(v)
    tree_arrows = [(v, p) for v, p in parent.items()]          # 부모가 자식을 읽는다
    assert is_linear_extension(reversed_preorder(0, children), list(range(n)), tree_arrows)
    assert minimal_elements(list(range(n)), tree_arrows) == {v for v in range(n) if not children[v]}  # 극소 원소 = 잎

# C2의 반례: g가 a, b를 읽고 a가 b를 읽는다. b를 먼저 방문한다.
g_children = {"g": ["a", "b"], "a": ["b"], "b": []}               # 스택이라 b가 먼저 나온다
c2_arrows = [("a", "g"), ("b", "g"), ("b", "a")]
pre = reversed_preorder("g", g_children)[::-1]
assert pre == ["g", "b", "a"]
assert pre[::-1] == ["a", "b", "g"] and not is_linear_extension(pre[::-1], ["g", "a", "b"], c2_arrows)
_, fin_c2 = memo_run("g", lambda s: {"g": ["b", "a"], "a": ["b"], "b": []}[s], lambda s, v: 0)
assert fin_c2 == ["b", "a", "g"] and is_linear_extension(fin_c2, ["g", "a", "b"], c2_arrows)
fails = 0
for _ in range(2000):                                            # 나무가 아니면 실제로 자주 틀린다
    n = rng.randint(3, 10)
    nodes_r, arrows_r = random_dag(n, 0.5)
    reads = defaultdict(list)
    for a, b in arrows_r:
        reads[b].append(a)
    goal = rng.randrange(n)
    sub = down_set(goal, arrows_r)
    order = reversed_preorder(goal, reads)
    sub_arrows = [(a, b) for a, b in arrows_r if a in sub and b in sub]
    if not is_linear_extension(order, list(sub), sub_arrows):
        fails += 1
assert fails > 0

# ----------------------------------- F. 고리: 기억하기는 끝없이 돈다, 칸은 남긴다
limit = sys.getrecursionlimit()
cost = [1, 2, 3, 4, 5]
try:
    memo_run(2, lambda x: [y for y in (x - 1, x + 1) if 0 <= y < len(cost)],
             lambda x, vals: cost[x] + (min(vals) if vals else 0))
    raise AssertionError("고리인데 재귀가 끝났다")
except RecursionError:
    pass
assert sys.getrecursionlimit() == limit
line_arrows = [(y, x) for x in range(5) for y in (x - 1, x + 1) if 0 <= y < 5]
order, left = kahn(list(range(5)), line_arrows)
assert order == [] and len(left) == 5 and has_cycle_three_colors(list(range(5)), line_arrows)

for _ in range(2000):                                            # 칸 알고리즘이 끝까지 감 ⇔ 고리 없음
    n = rng.randint(1, 9)
    arrows_r = [(a, b) for a in range(n) for b in range(n) if a != b and rng.random() < 0.2]
    order, left = kahn(list(range(n)), arrows_r)
    assert (not left) == (not has_cycle_three_colors(list(range(n)), arrows_r))
    if not left:
        assert is_linear_extension(order, list(range(n)), arrows_r)


# ------------------------------------------ G. 0-1 배낭: 제자리 갱신의 조건
def knap_1d(items, W, descending):
    dp = [0] * (W + 1)
    for w, v in items:
        rng_w = range(W, w - 1, -1) if descending else range(w, W + 1)
        for cap in rng_w:
            dp[cap] = max(dp[cap], dp[cap - w] + v)
    return dp[W]


assert knap_1d([(2, 3)], 4, descending=False) == 6                 # 같은 물건을 두 번 넣음
assert knap_1d([(2, 3)], 4, descending=True) == 3

for _ in range(800):
    n = rng.randint(1, 6)
    W = rng.randint(0, 15)
    items = [(rng.randint(1, 8), rng.randint(1, 20)) for _ in range(n)]
    best = max(sum(v for (w, v), t in zip(items, pick) if t)
               for pick in itertools.product([0, 1], repeat=n)
               if sum(w for (w, v), t in zip(items, pick) if t) <= W)
    # 2차원 표: dp[i][w]는 i - 1 줄만 읽으니 같은 줄 안의 순서는 아무래도 된다
    prev = [0] * (W + 1)
    for w_i, v_i in items:
        cur = [None] * (W + 1)
        caps = list(range(W + 1))
        rng.shuffle(caps)
        for cap in caps:
            cur[cap] = max(prev[cap], prev[cap - w_i] + v_i) if cap >= w_i else prev[cap]
        prev = cur
    assert prev[W] == best == knap_1d(items, W, descending=True)
    # 같은 줄의 칸끼리는 화살표가 없다
    arrows_k = [((i - 1, cap), (i, cap)) for i in range(1, n + 1) for cap in range(W + 1)]
    arrows_k += [((i - 1, cap - items[i - 1][0]), (i, cap)) for i in range(1, n + 1)
                 for cap in range(items[i - 1][0], W + 1)]
    assert all(a[0] == b[0] - 1 for a, b in arrows_k)


# ----------------------------------------- H. 네 방향 격자: 고리와 다익스트라
grid = [[1, 1, 1], [9, 9, 1], [1, 1, 1]]
R, Cn = 3, 3
cells_g = [(r, c) for r in range(R) for c in range(Cn)]


def nbrs(r, c):
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if 0 <= r + dr < R and 0 <= c + dc < Cn:
            yield r + dr, c + dc


grid_arrows = [(u, v) for v in cells_g for u in nbrs(*v)]
assert has_cycle_three_colors(cells_g, grid_arrows) and kahn(cells_g, grid_arrows)[1]
one_pass = {}
for r, c in cells_g:                                    # 행 순서로 한 번 훑기(채운 이웃만 읽음)
    if (r, c) == (0, 0):
        one_pass[r, c] = grid[0][0]
        continue
    assert {u for u in nbrs(r, c) if u in one_pass} <= {(r - 1, c), (r, c - 1)}   # 위·왼쪽만 채워져 있다
    one_pass[r, c] = grid[r][c] + min(one_pass.get(u, INF) for u in nbrs(r, c))
dist = {(0, 0): grid[0][0]}
pq = [(grid[0][0], (0, 0))]
done = set()
while pq:
    dd, u = heapq.heappop(pq)
    if u in done:
        continue
    done.add(u)
    for v in nbrs(*u):
        nd = dd + grid[v[0]][v[1]]
        if nd < dist.get(v, INF):
            dist[v] = nd
            heapq.heappush(pq, (nd, v))
assert one_pass[2, 0] == 11 and dist[2, 0] == 7


# ---------------------- I. 입력 그래프의 고리 vs 상태의 고리: 플로이드–워셜, 벨만–포드
fw_edges = {(1, 2): 1, (2, 3): 1, (1, 3): 5, (3, 1): 1}        # 27 C1: 1 → 2 → 3 → 1 고리
assert has_cycle_three_colors([1, 2, 3], list(fw_edges))
n = 3
states = [(k, i, j) for k in range(n + 1) for i in range(1, n + 1) for j in range(1, n + 1)]
fw_arrows = []
for k, i, j in states:
    if k:
        for s in ((k - 1, i, j), (k - 1, i, k), (k - 1, k, j)):
            fw_arrows.append((s, (k, i, j)))
assert not has_cycle_three_colors(states, fw_arrows)
assert all(a[0] < b[0] for a, b in fw_arrows)                     # k가 늘 커진다
# k를 바깥에 두는 순서(k, i, j)는 선형 확장, k를 안쪽에 두는 순서(i, j, k)는 아니다.
# k = 0 칸(처음 표)은 미리 채워져 있으니 k ≥ 1 칸만 줄 세운다.
for n4 in range(2, 6):
    st = [(k, i, j) for k in range(1, n4 + 1) for i in range(1, n4 + 1) for j in range(1, n4 + 1)]
    ar = [(s, (k, i, j)) for k, i, j in st if k >= 2
          for s in ((k - 1, i, j), (k - 1, i, k), (k - 1, k, j))]
    assert is_linear_extension(sorted(st), st, ar)
    inner = sorted(st, key=lambda s: (s[1], s[2], s[0]))
    assert not is_linear_extension(inner, st, ar)
    pos = {s: t for t, s in enumerate(inner)}
    # 본문의 설명: k > j이면 (k, i, j)가 읽는 (k − 1, i, k)가 뒤에 있다(빈 칸)
    for k, i, j in st:
        if k > j:
            assert pos[(k - 1, i, k)] > pos[(k, i, j)]
bf_states = [(t, v) for t in range(n) for v in range(1, n + 1)]
bf_arrows = [((t - 1, u), (t, v)) for t in range(1, n) for (u, v) in fw_edges]
bf_arrows += [((t - 1, v), (t, v)) for t in range(1, n) for v in range(1, n + 1)]
assert not has_cycle_three_colors(bf_states, bf_arrows)


def fw(n, edges, k_outer):
    Dm = [[0 if i == j else edges.get((i, j), INF) for j in range(n + 1)] for i in range(n + 1)]
    if k_outer:
        for k in range(1, n + 1):
            for i in range(1, n + 1):
                for j in range(1, n + 1):
                    Dm[i][j] = min(Dm[i][j], Dm[i][k] + Dm[k][j])
    else:
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                for k in range(1, n + 1):
                    Dm[i][j] = min(Dm[i][j], Dm[i][k] + Dm[k][j])
    return Dm


assert fw(3, fw_edges, True)[1][1:] == [0, 1, 2]
c3 = {(1, 2): 4, (2, 4): 1, (4, 3): 5}                            # 27 C3
assert fw(4, c3, True)[1][3] == 10 and fw(4, c3, False)[1][3] == INF


# ------------------------- J. 늘 커지는 값 f: 코딩 테스트 공부와 무작위 DAG
def study_dp(alp, cop, problems, key):
    A = max(p[0] for p in problems)
    Cc = max(p[1] for p in problems)
    alp, cop = min(alp, A), min(cop, Cc)
    dp = {(a, c): INF for a in range(A + 1) for c in range(Cc + 1)}
    dp[alp, cop] = 0
    arrows = []
    for a, c in sorted(dp, key=key):
        moves = []
        if a < A:
            moves.append(((a + 1, c), 1))
        if c < Cc:
            moves.append(((a, c + 1), 1))
        for ra, rc, wa, wc, t in problems:
            if a >= ra and c >= rc:
                moves.append(((min(A, a + wa), min(Cc, c + wc)), t))
        for nxt, t in moves:
            if nxt == (a, c):                         # 제자리로 돌아오는 화살표는 뺀다
                assert t >= 1                         # 시간이 1 이상이라 답을 줄이지 못한다
                continue
            arrows.append(((a, c), nxt))
            if dp[a, c] + t < dp[nxt]:
                dp[nxt] = dp[a, c] + t
    return dp[A, Cc], arrows, dp


def study_dijkstra(alp, cop, problems):
    A = max(p[0] for p in problems)
    Cc = max(p[1] for p in problems)
    start = (min(alp, A), min(cop, Cc))
    dist = {start: 0}
    pq = [(0, start)]
    while pq:
        d0, (a, c) = heapq.heappop(pq)
        if d0 > dist[a, c]:
            continue
        moves = [((min(A, a + 1), c), 1), ((a, min(Cc, c + 1)), 1)]
        moves += [((min(A, a + wa), min(Cc, c + wc)), t) for ra, rc, wa, wc, t in problems if a >= ra and c >= rc]
        for nxt, t in moves:
            if d0 + t < dist.get(nxt, INF):
                dist[nxt] = d0 + t
                heapq.heappush(pq, (d0 + t, nxt))
    return dist[A, Cc]


lex = lambda s: s                       # noqa: E731  a, c 사전 순
diag = lambda s: (s[0] + s[1], s[0])    # noqa: E731  a + c 순
ex = [[10, 15, 2, 1, 2], [20, 20, 3, 3, 4]]
assert study_dp(10, 10, ex, lex)[0] == 15 == study_dp(10, 10, ex, diag)[0] == study_dijkstra(10, 10, ex)
for _ in range(600):
    probs = [[rng.randint(0, 25), rng.randint(0, 25), rng.randint(0, 6), rng.randint(0, 6), rng.randint(1, 10)]
             for _ in range(rng.randint(1, 5))]
    alp, cop = rng.randint(0, 25), rng.randint(0, 25)
    r1, arrows_s, _ = study_dp(alp, cop, probs, lex)
    r2, _, _ = study_dp(alp, cop, probs, diag)
    assert r1 == r2 == study_dijkstra(alp, cop, probs)
    assert all(b[0] + b[1] > a[0] + a[1] and b > a for a, b in arrows_s)   # a + c도, 사전 순도 늘 커진다
    assert all(b[0] >= a[0] and b[1] >= a[1] for a, b in arrows_s)          # a, c는 줄지 않는다

for _ in range(1500):                    # f가 화살표마다 커지면 f 순서(같은 값끼리는 아무렇게나)가 선형 확장
    n = rng.randint(1, 12)
    nodes_r, arrows_r = random_dag(n, rng.random() * 0.6)
    topo, left = kahn(nodes_r, arrows_r)
    assert not left
    preds = defaultdict(list)
    for a, b in arrows_r:
        preds[b].append(a)
    depth, f = {}, {}
    for v in topo:
        depth[v] = 1 + max((depth[u] for u in preds[v]), default=0)
        f[v] = max((f[u] for u in preds[v]), default=0) + rng.randint(1, 3)
    for key in (depth, f):
        assert all(key[a] < key[b] for a, b in arrows_r)
        order = sorted(nodes_r, key=lambda v: (key[v], rng.random()))
        assert is_linear_extension(order, nodes_r, arrows_r)


# ----------------- K. 번호로 순서가 안 보이는 DAG: 칸 알고리즘 순서로 길의 수 세기
def count_paths_brute(s, t, out):
    if s == t:
        return 1
    return sum(count_paths_brute(w, t, out) for w in out[s])


for _ in range(800):
    n = rng.randint(2, 10)
    nodes_r, arrows_r = random_dag(n, 0.4)
    out = defaultdict(list)
    for a, b in arrows_r:
        out[a].append(b)
    s, t = rng.sample(nodes_r, 2)
    topo, _ = kahn(nodes_r, arrows_r)
    ways = {v: 0 for v in nodes_r}
    ways[s] = 1
    for v in topo:
        for w in out[v]:
            ways[w] += ways[v]
    assert ways[t] == count_paths_brute(s, t, out)


# ------------------------------------------------------------ L. 전이 문제
W_, P_, M_, S_, G_, D_ = "물", "파썰기", "면", "스프", "파올리기", "담기"
steps = [W_, P_, M_, S_, G_, D_]
rec = [(W_, M_), (W_, S_), (M_, G_), (P_, G_), (S_, D_), (G_, D_)]
les_r = linear_extensions(steps, rec)
assert len(les_r) == 11
assert is_linear_extension([W_, P_, M_, S_, G_, D_], steps, rec)
assert is_linear_extension([P_, W_, S_, M_, G_, D_], steps, rec)
preds = defaultdict(list)
for a, b in rec:
    preds[b].append(a)
tmin, fin_t = memo_run(D_, lambda v: preds[v], lambda v, vals: 1 + max(vals, default=0))
assert {v: tmin[v] for v in steps} == {W_: 1, P_: 1, M_: 2, S_: 2, G_: 3, D_: 4}
assert is_linear_extension(fin_t, steps, rec)
# 4분이면 된다: 분마다 앞 단계가 끝난 일을 모두 한다
done_at = {}
minute = 0
while len(done_at) < len(steps):
    minute += 1
    now = [v for v in steps if v not in done_at and all(u in done_at for u in preds[v])]
    for v in now:
        done_at[v] = minute
assert minute == 4 and done_at == tmin
# 사슬 물 → 면 → 파 올리기 → 담기는 하나씩 차례로 해야 한다
assert all(p in rec for p in [(W_, M_), (M_, G_), (G_, D_)])
# "물은 파를 올린 뒤에 끓인다"를 더하면 고리
rec2 = rec + [(G_, W_)]
order2, left2 = kahn(steps, rec2)
assert order2 == [P_] and set(left2) == {W_, M_, S_, G_, D_}
assert has_cycle_three_colors(steps, rec2) and linear_extensions(steps, rec2) == []
preds2 = defaultdict(list)
for a, b in rec2:
    preds2[b].append(a)
try:
    memo_run(D_, lambda v: preds2[v], lambda v, vals: 1 + max(vals, default=0))
    raise AssertionError("고리인데 재귀가 끝났다")
except RecursionError:
    pass

print("ALL CHECKS PASSED")
