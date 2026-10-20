"""40.추이 폐포 ↔ 플로이드–워셜: 비교 표, 대응, 깨지는 곳, 연산 짝 표, 전이 문제, 카드 답을 확인한다.

점 번호는 문서와 같이 1부터 센다(0번 칸은 쓰지 않는다).
"""
import itertools
import math
import random
from fractions import Fraction

INF = float("inf")
rng = random.Random(40)


def OR(a, b):
    return a or b


def AND(a, b):
    return a and b


def ADD(a, b):
    return a + b


def MUL(a, b):
    return a * b


def run(n, T, plus, times, order="kij", snapshots=None, rounds=None):
    """같은 세 겹 반복. plus = 고르기, times = 잇기. 표 T를 제자리에서 고친다."""
    count = 0
    if order == "kij":
        for k in range(1, n + 1):
            before = [row[:] for row in T]
            for i in range(1, n + 1):
                for j in range(1, n + 1):
                    T[i][j] = plus(T[i][j], times(T[i][k], T[k][j]))
                    count += 1
            if snapshots is not None:
                snapshots.append([row[1:] for row in T[1:]])
            if rounds is not None:
                rounds.append((k, before, [row[:] for row in T]))
    else:  # i, j, k: k를 가장 안쪽에 둔 잘못된 순서
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                for k in range(1, n + 1):
                    T[i][j] = plus(T[i][j], times(T[i][k], T[k][j]))
                    count += 1
    run.count = count
    return T


def warshall(n, rel, diag_one=False, order="kij", snapshots=None, rounds=None):
    T = [[False] * (n + 1) for _ in range(n + 1)]
    for a, b in rel:
        T[a][b] = True
    if diag_one:
        for i in range(1, n + 1):
            T[i][i] = True
    return run(n, T, OR, AND, order, snapshots, rounds)


def warshall_layers(n, rel):
    """정의 그대로: T_k를 T_{k-1}에서 새 표로 만든다."""
    T = [[False] * (n + 1) for _ in range(n + 1)]
    for a, b in rel:
        T[a][b] = True
    for k in range(1, n + 1):
        T = [[T[i][j] or (T[i][k] and T[k][j]) if i and j else False
              for j in range(n + 1)] for i in range(n + 1)]
    return T


def floyd(n, edges, diag_zero=True, snapshots=None, rounds=None):
    D = [[INF] * (n + 1) for _ in range(n + 1)]
    if diag_zero:
        for i in range(1, n + 1):
            D[i][i] = 0
    for a, b, w in edges:
        D[a][b] = min(D[a][b], w)
    return run(n, D, min, ADD, "kij", snapshots, rounds)


def pairs_of(T, n):
    return {(i, j) for i in range(1, n + 1) for j in range(1, n + 1) if T[i][j]}


def reach_plus(n, rel):
    """점마다 탐색해 한 걸음 이상 가는 짝을 모은다(R⁺)."""
    succ = {i: set() for i in range(1, n + 1)}
    for a, b in rel:
        succ[a].add(b)
    res = set()
    for s in range(1, n + 1):
        seen, stack = set(), list(succ[s])
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            stack.extend(succ[v])
        res |= {(s, v) for v in seen}
    return res


def has_neg_cycle(n, edges):
    d = [0] * (n + 1)                      # 모든 점에서 동시에 출발
    for _ in range(n):
        changed = False
        for a, b, w in edges:
            if d[a] + w < d[b]:
                d[b] = d[a] + w
                changed = True
        if not changed:
            return False
    return True


def bellman_ford(n, edges, s):
    d = [INF] * (n + 1)
    d[s] = 0
    for _ in range(n - 1):
        for a, b, w in edges:
            if d[a] + w < d[b]:
                d[b] = d[a] + w
    return d


def rand_rel(n, p, loops=True):
    return [(a, b) for a in range(1, n + 1) for b in range(1, n + 1)
            if (loops or a != b) and rng.random() < p]


def simple_paths(n, adj, s, t):
    """s에서 t로 가는, 같은 점을 두 번 지나지 않는 길(한 걸음 이상)의 간선 값 목록."""
    out = []

    def go(v, seen, ws):
        for u, w in adj[v]:
            if u == t:
                out.append(ws + [w])
            elif u not in seen:
                go(u, seen | {u}, ws + [w])

    go(s, {s}, [])
    return out


def adjacency(n, edges):
    adj = {i: [] for i in range(1, n + 1)}
    for a, b, w in edges:
        adj[a].append((b, w))
    return adj


# ---------- 1. 먼저 비교해 보기: 1→2(2), 2→3(3), 3→4(1), 1→4(9) ----------
rel = [(1, 2), (2, 3), (3, 4), (1, 4)]
edges = [(1, 2, 2), (2, 3, 3), (3, 4, 1), (1, 4, 9)]
snapW, snapF = [], []
T = warshall(4, rel, snapshots=snapW)
D = floyd(4, edges, snapshots=snapF)
init = set(rel)


def as_pairs(snap):
    return {(i + 1, j + 1) for i in range(4) for j in range(4) if snap[i][j]}


assert as_pairs(snapW[0]) == init                                  # 1을 거쳐도 됨: 그대로
assert as_pairs(snapW[1]) == init | {(1, 3)}                       # 2까지: (1,3)
assert as_pairs(snapW[2]) == init | {(1, 3), (2, 4)}               # 3까지: (2,4)
assert as_pairs(snapW[3]) == as_pairs(snapW[2])                    # 4까지: 그대로
assert pairs_of(T, 4) == {(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)}
D0 = [[0, 2, INF, 9], [INF, 0, 3, INF], [INF, INF, 0, 1], [INF, INF, INF, 0]]
assert snapF[0] == D0                                              # 1을 거쳐도 됨: 그대로
assert snapF[1][0][2] == 5 and sum(snapF[1][i][j] != D0[i][j] for i in range(4) for j in range(4)) == 1
assert snapF[2][1][3] == 4 and snapF[2][0][3] == 6 == min(9, 5 + 1)
assert sum(snapF[2][i][j] != snapF[1][i][j] for i in range(4) for j in range(4)) == 2
assert snapF[3] == snapF[2]
assert D[1][2:] == [2, 5, 6] and D[2][3:] == [3, 4] and D[3][4] == 1
assert {(i, j) for i in range(1, 5) for j in range(1, 5) if i != j and D[i][j] < INF} == pairs_of(T, 4)
# 결과 줄: 대각선 0으로 시작했으니 ∞가 아닌 칸은 대각선 밖 6칸 + 대각선 4칸이다(대각선 밖에서만 6칸)
assert {(i, j) for i in range(1, 5) for j in range(1, 5) if D[i][j] < INF} == pairs_of(T, 4) | {(i, i) for i in range(1, 5)}
assert sum(D[i][j] < INF for i in range(1, 5) for j in range(1, 5)) == 10
# 관계와 그 성질 예제의 사슬(지름길 없음)도 6쌍
assert pairs_of(warshall(4, [(1, 2), (2, 3), (3, 4)]), 4) == pairs_of(T, 4)
# 세 겹 반복은 n³번 고친다
warshall(7, []); assert run.count == 7 ** 3

# ---------- 2. 길이 있는지만 보면 늘 같다(음수 사이클, 제자리 갱신 포함) ----------
neg_graphs = 0
for trial in range(1500):
    n = rng.randint(1, 7)
    es = [(a, b, rng.randint(-5, 10)) for a in range(1, n + 1) for b in range(1, n + 1)
          if rng.random() < 0.35]
    r = [(a, b) for a, b, _ in es]
    neg_graphs += has_neg_cycle(n, es)
    for diag_zero in (True, False):
        sF, sW = [], []
        floyd(n, es, diag_zero=diag_zero, snapshots=sF)
        warshall(n, r, diag_one=diag_zero, snapshots=sW)
        for a, b in zip(sF, sW):                                   # 매 바퀴마다
            assert [[x < INF for x in row] for row in a] == b
    Rp = reach_plus(n, r)
    Tg = warshall(n, r)
    assert pairs_of(Tg, n) == Rp                                   # 대각선 그대로 → R⁺
    assert pairs_of(warshall(n, r, diag_one=True), n) == Rp | {(i, i) for i in range(1, n + 1)}  # → R*
    assert pairs_of(warshall_layers(n, r), n) == Rp                # 제자리 = 정의대로 새 표
    for i in range(1, n + 1):                                      # R⁺[i][i] ⇔ 한 걸음 이상 걸어 돌아옴
        back = any(a == i and (j == i or (j, i) in Rp) for a, j in r)
        assert Tg[i][i] == back
assert neg_graphs > 200

# ---------- 3. 대각선을 ∞로 시작하면 대각선 = i를 지나는 가장 싼 고리 ----------
checked = 0
for trial in range(1500):
    n = rng.randint(1, 7)
    es = [(a, b, rng.randint(-3, 10)) for a in range(1, n + 1) for b in range(1, n + 1)
          if rng.random() < 0.35]
    if has_neg_cycle(n, es):
        continue
    checked += 1
    Dz = floyd(n, es, diag_zero=True)
    Di = floyd(n, es, diag_zero=False)
    dist = {s: bellman_ford(n, es, s) for s in range(1, n + 1)}
    for i in range(1, n + 1):
        cyc = min([dist[i][a] + w for a, b, w in es if b == i], default=INF)
        assert Di[i][i] == cyc
        assert Dz[i][i] == 0
        for j in range(1, n + 1):
            if i != j:
                assert Di[i][j] == Dz[i][j] == dist[i][j]
    # 음수 사이클이 없으면 끝난 표는 삼각 부등식을 지킨다(추이성의 거리판)
    for i, j, k in itertools.product(range(1, n + 1), repeat=3):
        assert Dz[i][j] <= Dz[i][k] + Dz[k][j]
assert checked > 800
for trial in range(300):                                           # R⁺는 추이적
    n = rng.randint(1, 7)
    Tg = warshall(n, rand_rel(n, 0.3))
    for i, j, k in itertools.product(range(1, n + 1), repeat=3):
        assert not (Tg[i][k] and Tg[k][j]) or Tg[i][j]

# ---------- 4. 최단 거리표는 "삼각 부등식 + 간선 비용 이하" 표 가운데 칸마다 가장 큰 표 ----------
DOM = [-1, 0, 1, 2, 3, 4, INF]
# 대각선은 훑지 않아도 된다: 삼각 부등식 d[i][i] ≤ d[i][i] + d[i][i]는 d[i][i] ≥ 0일 때만 맞고,
# 처음 표에서 d[i][i] ≤ 0이라 대각선은 0으로 정해진다
assert [x for x in DOM if x <= 0 and x <= x + x] == [0]
off = [(i, j) for i in range(1, 4) for j in range(1, 4) if i != j]
for trial in range(12):
    es = [(a, b, rng.randint(1, 2)) for a, b in off if rng.random() < 0.6]
    Dz = floyd(3, es)
    E0 = floyd(3, [])
    for a, b, w in es:
        E0[a][b] = min(E0[a][b], w)
    choices = [[v for v in DOM if v <= E0[i][j]] for i, j in off]
    best = {c: -INF for c in off}
    for vals in itertools.product(*choices):
        d = [[0] * 4 for _ in range(4)]
        for (i, j), v in zip(off, vals):
            d[i][j] = v
        if all(d[i][j] <= d[i][k] + d[k][j] for i, j, k in itertools.product(range(1, 4), repeat=3)):
            for (i, j), v in zip(off, vals):
                best[(i, j)] = max(best[(i, j)], v)
    assert all(best[(i, j)] == Dz[i][j] for i, j in off)            # 가장 큰 것이 바로 최단 거리표

# ---------- 5. 음수 사이클: 1→2(1), 2→3(−3), 3→1(1) ----------
neg = [(1, 2, 1), (2, 3, -3), (3, 1, 1)]
rounds = []
Dn = floyd(3, neg, rounds=rounds)
assert any(Dn[i][i] < 0 for i in range(1, 4))
k, before, after = rounds[2]
assert k == 3 and before[1][3] == -2 and after[1][3] == -3          # 3번째 바퀴에 3번 열이 바뀐다
assert before[3][3] == -1                                           # 그 바퀴를 시작할 때 D[3][3] < 0
assert pairs_of(warshall(3, [(a, b) for a, b, _ in neg]), 3) == set(itertools.product(range(1, 4), repeat=2))
# 와셜은 k번째 바퀴에 k행·k열이 늘 그대로(흡수 법칙 a ∨ (a ∧ b) = a)
for trial in range(800):
    n = rng.randint(1, 7)
    rr = []
    warshall(n, rand_rel(n, 0.35), rounds=rr)
    for k, b, a in rr:
        assert all(b[i][k] == a[i][k] and b[k][i] == a[k][i] for i in range(1, n + 1))
for x, y in itertools.product([False, True], repeat=2):
    assert (x or (x and y)) == x
# 플로이드–워셜은 바퀴를 시작할 때 D[k][k] ≥ 0이면 그대로, 음수면 바뀔 수 있다
moved = 0
for trial in range(800):
    n = rng.randint(1, 7)
    es = [(a, b, rng.randint(-5, 10)) for a in range(1, n + 1) for b in range(1, n + 1)
          if a != b and rng.random() < 0.35]
    rr = []
    floyd(n, es, rounds=rr)
    for k, b, a in rr:
        same = all(b[i][k] == a[i][k] and b[k][i] == a[k][i] for i in range(1, n + 1))
        if b[k][k] >= 0:
            assert same
        else:
            assert a[k][k] < b[k][k]                       # 음수면 D[k][k]부터 바뀐다
        moved += not same
assert moved > 0

# ---------- 6. 반복 순서: 27 C3의 반례가 와셜에서도 틀린다 ----------
r3 = [(1, 2), (2, 4), (4, 3)]
assert warshall(4, r3)[1][3] is True
assert warshall(4, r3, order="ijk")[1][3] is False

# ---------- 7. 비트 묶음 와셜 ----------
def warshall_bits(n, rel):
    rows = [0] * (n + 1)
    for a, b in rel:
        rows[a] |= 1 << b
    for k in range(1, n + 1):
        bit = 1 << k
        for i in range(1, n + 1):
            if rows[i] & bit:
                rows[i] |= rows[k]                 # i행에 k행을 한 번에 더한다
    return rows


for trial in range(400):
    n = rng.randint(1, 30)
    r = rand_rel(n, rng.choice([0.03, 0.1, 0.3]))
    rows = warshall_bits(n, r)
    Tg = warshall(n, r)
    assert all(bool(rows[i] >> j & 1) == Tg[i][j] for i in range(1, n + 1) for j in range(1, n + 1))

# ---------- 8. 연산 짝 표 ----------
# 고리 조건: 제자리 값 e와 고리 값 c를 고르면 e가 남는가
assert all((True or c) is True for c in (False, True))                          # 도달: 늘
assert all((min(0, c) == 0) == (c >= 0) for c in range(-10, 11))                 # 거리: c ≥ 0일 때만
assert all(min(0, c) == 0 for c in range(1, 11))                                 # 등산코스: 시간이 양수
assert all((1 + c == 1) == (c == 0) for c in range(0, 6))                        # 길의 수: c = 0일 때만
# 고르기를 두 번 해도 같은가(멱등): ∨, min, max는 그렇고 +는 아니다
assert all(min(a, a) == a and max(a, a) == a for a in range(-5, 6))
assert all((a or a) == a for a in (False, True)) and 1 + 1 != 1
# 분배법칙(잇기가 고르기에 나눠 들어간다)
vals = list(range(-4, 6)) + [INF]
for a, b, c in itertools.product(vals, repeat=3):
    assert a + min(b, c) == min(a + b, a + c)
    assert max(a, min(b, c)) == min(max(a, b), max(a, c))
for a, b, c in itertools.product([False, True], repeat=3):
    assert (a and (b or c)) == ((a and b) or (a and c))
fr = [Fraction(k, 10) for k in range(0, 11)]
for a, b, c in itertools.product(fr, repeat=3):
    assert a * max(b, c) == max(a * b, a * c)
    assert a * (b + c) == a * b + a * c

# 가장 긴 구간의 최소(min, max): 길 없음 ∞, 제자리 0
for trial in range(500):
    n = rng.randint(2, 6)
    es = [(a, b, rng.randint(1, 10)) for a in range(1, n + 1) for b in range(1, n + 1)
          if a != b and rng.random() < 0.4]
    M = [[INF] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        M[i][i] = 0
    for a, b, w in es:
        M[a][b] = min(M[a][b], w)
    run(n, M, min, max)
    adj = adjacency(n, es)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                assert M[i][j] == min((max(p) for p in simple_paths(n, adj, i, j)), default=INF)

# 길의 수(+, ×): 고리 없는 그래프에서 제자리 0이면 맞다
for trial in range(500):
    n = rng.randint(2, 7)
    perm = list(range(1, n + 1))
    rng.shuffle(perm)
    es = [(perm[x], perm[y], 1) for x in range(n) for y in range(x + 1, n) if rng.random() < 0.5]
    N = [[0] * (n + 1) for _ in range(n + 1)]
    for a, b, _ in es:
        N[a][b] = 1
    run(n, N, ADD, MUL)
    adj = adjacency(n, es)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            assert N[i][j] == (len(simple_paths(n, adj, i, j)) if i != j else 0)
# 제자리를 1로 두면 고리가 없어도 같은 길을 두 번 센다: 1→2 하나뿐인데
N = [[0, 0, 0], [0, 1, 1], [0, 0, 1]]
run(2, N, ADD, MUL)
assert N[1][2] != 1 and N[1][1] != 1

# ---------- 9. 카드 ----------
# C1: min도 멱등이니 a ∨ a = a로는 둘을 가르지 못한다. 음수 고리는 돌 때마다 더 줄어든다.
c = -1
assert min(0, c) == c and c + c < c
# C2: 1→2(1), 2→1(4), 2→3(2), 대각선 ∞로 시작
c2 = [(1, 2, 1), (2, 1, 4), (2, 3, 2)]
Dc = floyd(3, c2, diag_zero=False)
assert [Dc[1][1:], Dc[2][1:], Dc[3][1:]] == [[5, 1, 3], [4, 5, 2], [INF, INF, INF]]
Rc = {(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)}
assert reach_plus(3, [(a, b) for a, b, _ in c2]) == Rc
assert {(i, j) for i in range(1, 4) for j in range(1, 4) if Dc[i][j] < INF} == Rc
Dz = floyd(3, c2)
assert {(i, j) for i in range(1, 4) for j in range(1, 4) if Dz[i][j] < INF} == Rc | {(3, 3)}
# C3: 1→2, 2→1에서 (+, ×) 반복은 [[1, 2], [2, 2]]
N = [[0, 0, 0], [0, 0, 1], [0, 1, 0]]
run(2, N, ADD, MUL)
assert [N[1][1:], N[2][1:]] == [[1, 2], [2, 2]]
adj2 = adjacency(2, [(1, 2, 1), (2, 1, 1)])
assert len(simple_paths(2, adj2, 1, 2)) == 1
walks = [sum(1 for L in range(1, M + 1) if L % 2 == 1) for M in (1, 3, 5, 7)]   # 1에서 2로 가는 보행은 홀수 걸음
assert walks == [1, 2, 3, 4]                                                     # 걸음 수를 늘리면 끝없이 는다

# ---------- 10. 전이 문제: 가장 믿을 만한 경로(max, ×) ----------
F = Fraction
links = [(1, 2, F(9, 10)), (2, 3, F(9, 10)), (1, 3, F(7, 10)), (3, 4, F(4, 5)), (2, 4, F(1, 2))]


def reliability(n, und):
    P = [[F(0)] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        P[i][i] = F(1)
    for a, b, p in und:
        P[a][b] = max(P[a][b], p)
        P[b][a] = max(P[b][a], p)
    return run(n, P, max, MUL)


P = reliability(4, links)
assert P[1][4] == F(648, 1000) and P[1][3] == F(81, 100)
assert F(7, 10) * F(4, 5) == F(56, 100) and F(9, 10) * F(1, 2) == F(45, 100)   # 1–3–4, 1–2–4
for trial in range(400):
    n = rng.randint(2, 6)
    und = [(a, b, F(rng.randint(1, 10), 10)) for a in range(1, n + 1) for b in range(a + 1, n + 1)
           if rng.random() < 0.5]
    P = reliability(n, und)
    es = [(a, b, p) for a, b, p in und] + [(b, a, p) for a, b, p in und]
    adj = adjacency(n, es)
    Dl = floyd(n, [(a, b, -math.log(p)) for a, b, p in es])     # −ln p로 바꾸면 비용 0 이상인 최단 거리
    assert all(-math.log(p) >= 0 for _, _, p in es)
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            if i != j:
                best = max((math.prod(p) for p in simple_paths(n, adj, i, j)), default=F(0))
                assert P[i][j] == best
                assert (best == 0 and Dl[i][j] == INF) or abs(math.exp(-Dl[i][j]) - float(best)) < 1e-9
            else:
                assert P[i][i] == 1                                # 고리는 1을 넘지 못한다

# 환율(1보다 클 수 있음): 곱이 1보다 큰 고리 ⇔ 끝난 표에 P[i][i] > 1
rate = [[F(0)] * 3 for _ in range(3)]
rate[1][1] = rate[2][2] = F(1)
rate[1][2], rate[2][1] = F(2), F(3, 5)
run(2, rate, max, MUL)
assert rate[1][1] == F(6, 5) and F(2) * F(3, 5) == F(6, 5)
for trial in range(400):
    n = rng.randint(2, 5)
    es = [(a, b, F(rng.randint(5, 15), 10)) for a in range(1, n + 1) for b in range(1, n + 1)
          if a != b and rng.random() < 0.5]
    R = [[F(0)] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        R[i][i] = F(1)
    for a, b, x in es:
        R[a][b] = max(R[a][b], x)
    run(n, R, max, MUL)
    W = {(a, b): x for a, b, x in es}
    gain = False
    for L in range(2, n + 1):
        for cyc in itertools.permutations(range(1, n + 1), L):
            ok = all((cyc[t], cyc[(t + 1) % L]) in W for t in range(L))
            if ok and math.prod(W[(cyc[t], cyc[(t + 1) % L])] for t in range(L)) > 1:
                gain = True
    assert gain == any(R[i][i] > 1 for i in range(1, n + 1))
# −ln을 씌우면 곱이 합이 된다: 곱 > 1인 고리 ⇔ 비용 합 < 0인 고리, 확률(≤ 1) ⇔ 비용 ≥ 0
for trial in range(2000):
    xs = [F(rng.randint(5, 15), 10) for _ in range(rng.randint(1, 5))]
    prod = math.prod(xs)
    if prod != 1:
        assert (prod > 1) == (sum(-math.log(x) for x in xs) < 0)
    assert all((x <= 1) == (-math.log(x) >= -1e-12) for x in xs)

print("ALL CHECKS PASSED")
