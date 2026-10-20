"""37.누적 합 ↔ 아래삼각행렬: 문서의 대응표, 수치, 반례, 전이 문제, 카드의 값을 확인한다.

칸 번호는 0부터 센다(문서와 같다). 행렬 계산은 정수와 Fraction으로 정확하게 한다.
"""
import random
from fractions import Fraction as Fr
from itertools import accumulate

random.seed(37)


# ---------- 행렬 도구 ----------
def zeros(r, c):
    return [[0] * c for _ in range(r)]


def eye(n):
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def matmul(A, B):
    assert len(A[0]) == len(B), "차원 불일치"
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]


def matvec(A, x):
    assert len(A[0]) == len(x), "차원 불일치"
    return [sum(A[i][k] * x[k] for k in range(len(x))) for i in range(len(A))]


def transpose(A):
    return [list(r) for r in zip(*A)]


def outer(u, w):
    return [[ui * wj for wj in w] for ui in u]


def e(n, i):
    v = [0] * n
    v[i] = 1
    return v


def vsub(u, w):
    return [a - b for a, b in zip(u, w)]


def scal(x, v):
    return [x * t for t in v]


def L(n):
    """대각선과 그 아래가 모두 1인 n x n 아래삼각행렬."""
    return [[1 if j <= i else 0 for j in range(n)] for i in range(n)]


def Linv(n):
    """대각선 1, 바로 아래 -1인 두 대각 행렬."""
    return [[1 if j == i else (-1 if j == i - 1 else 0) for j in range(n)] for i in range(n)]


def M(n):
    """a -> P (길이 n+1, P[0] = 0): L 위에 0행을 붙인 (n+1) x n 행렬."""
    return [[0] * n] + L(n)


def B(n):
    """P -> a (a[i] = P[i+1] - P[i]): n x (n+1) 행렬."""
    return [[1 if j == i + 1 else (-1 if j == i else 0) for j in range(n + 1)] for i in range(n)]


def nnz(A):
    return sum(1 for r in A for x in r if x != 0)


def prefix(a):
    return list(accumulate(a, initial=0))


# ---------- 1. 비교 표의 값 ----------
a = [3, 1, 4]
assert prefix(a) == [0, 3, 4, 8]
assert matvec(L(3), a) == [3, 4, 8]
assert L(3) == [[1, 0, 0], [1, 1, 0], [1, 1, 1]]
assert Linv(3) == [[1, 0, 0], [-1, 1, 0], [0, -1, 1]]
assert matvec(Linv(3), [3, 4, 8]) == [3, 1, 4]
P = prefix(a)
assert [P[i + 1] - P[i] for i in range(3)] == [3, 1, 4]

# 구간 더하기: 길이 3인 0 배열의 1 ~ 2번에 2
D = [0] * 4
D[1] += 2
D[3] -= 2
assert D == [0, 2, 0, -2]
assert list(accumulate(D[:3])) == [0, 2, 2]
assert matvec(L(4), scal(2, vsub(e(4, 1), e(4, 3)))) == [0, 2, 2, 0]

# 2차원 3 x 3: (0, 0) ~ (1, 1)에 1
u = [1, 0, -1]
marks = outer(u, u)
assert marks == [[1, 0, -1], [0, 0, 0], [-1, 0, 1]]
horiz = matmul(marks, transpose(L(3)))          # 가로 누적 = 오른쪽에 L^T
assert horiz == [[1, 1, 0], [0, 0, 0], [-1, -1, 0]]
final = matmul(L(3), horiz)                     # 세로 누적 = 왼쪽에 L
assert final == [[1, 1, 0], [1, 1, 0], [0, 0, 0]]
Lu = matvec(L(3), u)
assert Lu == [1, 1, 0]
assert final == outer(Lu, Lu)

# 19 문서의 2차원 예시와 같은지: 19의 rect_add 방식(4 x 4 표시판, 가로 다음 세로)
def rect_add(n, m, updates):
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for r1, c1, r2, c2, x in updates:
        D[r1][c1] += x
        D[r1][c2 + 1] -= x
        D[r2 + 1][c1] -= x
        D[r2 + 1][c2 + 1] += x
    for i in range(n + 1):
        for j in range(1, m + 1):
            D[i][j] += D[i][j - 1]
    for j in range(m + 1):
        for i in range(1, n + 1):
            D[i][j] += D[i - 1][j]
    return [row[:m] for row in D[:n]]


assert rect_add(3, 3, [(0, 0, 1, 1, 1)]) == final

# ---------- 2. 대응표: 무작위 2,000번 ----------
TRIALS = 2000
for _ in range(TRIALS):
    n = random.randint(1, 12)
    a = [random.randint(-50, 50) for _ in range(n)]
    P = prefix(a)
    p = P[1:]
    # 누적 = L a, 차분 = L^{-1} p, L L^{-1} = L^{-1} L = I
    assert matvec(L(n), a) == p
    assert matvec(Linv(n), p) == a
    assert matmul(L(n), Linv(n)) == eye(n) and matmul(Linv(n), L(n)) == eye(n)
    assert [P[i + 1] - P[i] for i in range(n)] == a
    # 구간 합 = (e_{r+1} - e_l)^T P
    l = random.randint(0, n - 1)
    r = random.randint(l, n - 1)
    row = vsub(e(n + 1, r + 1), e(n + 1, l))
    assert sum(x * y for x, y in zip(row, P)) == sum(a[l:r + 1]) == P[r + 1] - P[l]
    # 구간 더하기: L_{n+1} x (e_l - e_{r+1}) = l ~ r번만 x, 마지막 칸은 늘 0
    x = random.randint(-9, 9)
    img = matvec(L(n + 1), scal(x, vsub(e(n + 1, l), e(n + 1, r + 1))))
    assert img[:n] == [x if l <= i <= r else 0 for i in range(n)]
    assert img[n] == 0
    Dd = [0] * (n + 1)
    Dd[l] += x
    Dd[r + 1] -= x
    assert list(accumulate(Dd[:n])) == img[:n]
    # 선형성: 표시를 모두 모아 한 번 누적 = 따로 누적해 더하기 = 직접 더하기
    k = random.randint(1, 6)
    ups = []
    for _ in range(k):
        l2 = random.randint(0, n - 1)
        r2 = random.randint(l2, n - 1)
        ups.append((l2, r2, random.randint(-9, 9)))
    total = [0] * (n + 1)
    each = [0] * (n + 1)
    brute = [0] * n
    for l2, r2, x2 in ups:
        d = scal(x2, vsub(e(n + 1, l2), e(n + 1, r2 + 1)))
        total = [s + t for s, t in zip(total, d)]
        each = [s + t for s, t in zip(each, matvec(L(n + 1), d))]
        for i in range(l2, r2 + 1):
            brute[i] += x2
    assert matvec(L(n + 1), total) == each
    assert each[:n] == brute
    # 한 칸 바꾸기: P가 x L e_i만큼 바뀌고, 바뀌는 칸은 P[i+1..n]의 n - i칸
    i = random.randint(0, n - 1)
    x = random.choice([v for v in range(-9, 10) if v != 0])
    a2 = a[:]
    a2[i] += x
    P2 = prefix(a2)
    diff = [s - t for s, t in zip(P2[1:], P[1:])]
    assert diff == scal(x, matvec(L(n), e(n, i)))
    changed = [k2 for k2 in range(n + 1) if P2[k2] != P[k2]]
    assert changed == list(range(i + 1, n + 1)) and len(changed) == n - i
    # L e_i는 L의 i번 열: i번부터 끝까지 1
    assert matvec(L(n), e(n, i)) == [1 if t >= i else 0 for t in range(n)]

# ---------- 3. P[0]을 붙인 M, 차분 B: BM = I, MB != I, MB P = P - P[0] ----------
for n in range(1, 13):
    assert len(M(n)) == n + 1 and len(M(n)[0]) == n
    assert matmul(B(n), M(n)) == eye(n)
    assert matmul(M(n), B(n)) != eye(n + 1)
    for _ in range(50):
        a = [random.randint(-20, 20) for _ in range(n)]
        assert matvec(M(n), a) == prefix(a)
        Q = [random.randint(-20, 20) for _ in range(n + 1)]   # P[0]이 0이 아닐 수도 있는 아무 수열
        assert matvec(B(n), Q) == [Q[t + 1] - Q[t] for t in range(n)]
        assert matvec(M(n), matvec(B(n), Q)) == [q - Q[0] for q in Q]

# ---------- 4. 0이 아닌 칸 수와 계산 횟수 ----------
def forward_general(Lmat, b):
    """일반 아래삼각행렬(대각 1)의 전진 대입. 곱셈·뺄셈 횟수를 센다."""
    n = len(b)
    c = [0] * n
    ops = 0
    for i in range(n):
        s = b[i]
        for j in range(i):
            s -= Lmat[i][j] * c[j]
            ops += 2                      # 곱셈 1, 뺄셈 1
        c[i] = s
    return c, ops


def prefix_by_bidiagonal(a):
    """L^{-1} p = a를 위에서부터 푼다: p[i] = a[i] + p[i-1]. 덧셈 횟수를 센다."""
    p, adds = [], 0
    for i, x in enumerate(a):
        if i == 0:
            p.append(x)
        else:
            p.append(x + p[-1])
            adds += 1
    return p, adds


def difference_by_running(pv):
    """L a = p를 전진 대입으로 풀 때, 괄호 안 합이 p[i-1]임을 쓰면 앞 칸 빼기 한 번."""
    a, subs = [], 0
    for i, x in enumerate(pv):
        if i == 0:
            a.append(x)
        else:
            a.append(x - pv[i - 1])
            subs += 1
    return a, subs


for n in range(1, 41):
    assert nnz(L(n)) == n * (n + 1) // 2
    assert nnz(Linv(n)) == 2 * n - 1
    a = [random.randint(-30, 30) for _ in range(n)]
    pv = list(accumulate(a))
    # 0이 아닌 칸마다 한 번 곱하면 n(n+1)/2번
    mults = sum(1 for i in range(n) for j in range(n) if L(n)[i][j] != 0)
    assert mults == n * (n + 1) // 2
    got, adds = prefix_by_bidiagonal(a)
    assert got == pv and adds == n - 1
    # 일반 전진 대입: 2 * n(n-1)/2 = n(n-1) 번(약 n^2)
    c, ops = forward_general(L(n), pv)
    assert c == a and ops == n * (n - 1)
    # 08의 전진 대입 줄 c[i] = b[i] - (c[0] + ... + c[i-1])에서 괄호 = b[i-1]
    for i in range(1, n):
        assert sum(c[:i]) == pv[i - 1]
    d, subs = difference_by_running(pv)
    assert d == a and subs == n - 1

# ---------- 5. 2차원: 바깥곱, 두 누적 순서, 직사각형 합 ----------
def rect_sum_four(S, r1, c1, r2, c2):
    return S[r2 + 1][c2 + 1] - S[r1][c2 + 1] - S[r2 + 1][c1] + S[r1][c1]


def prefix2d(A):
    n, m = len(A), len(A[0])
    S = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            S[i + 1][j + 1] = A[i][j] + S[i][j + 1] + S[i + 1][j] - S[i][j]
    return S


for _ in range(TRIALS // 4):
    N, Mc = random.randint(1, 7), random.randint(1, 7)
    r1 = random.randint(0, N - 1); r2 = random.randint(r1, N - 1)
    c1 = random.randint(0, Mc - 1); c2 = random.randint(c1, Mc - 1)
    x = random.randint(-9, 9)
    uu = vsub(e(N + 1, r1), e(N + 1, r2 + 1))
    ww = vsub(e(Mc + 1, c1), e(Mc + 1, c2 + 1))
    Dm = [[x * t for t in rw] for rw in outer(uu, ww)]
    # 네 모서리: +, -, -, + 이고 나머지는 0
    corners = {(r1, c1): x, (r1, c2 + 1): -x, (r2 + 1, c1): -x, (r2 + 1, c2 + 1): x}
    for i in range(N + 1):
        for j in range(Mc + 1):
            assert Dm[i][j] == corners.get((i, j), 0)
    Lr, Lc = L(N + 1), L(Mc + 1)
    vert_first = matmul(matmul(Lr, Dm), transpose(Lc))
    horiz_first = matmul(Lr, matmul(Dm, transpose(Lc)))
    assert vert_first == horiz_first                       # 결합법칙
    ind_r, ind_c = matvec(Lr, uu), matvec(Lc, ww)
    assert ind_r == [1 if r1 <= i <= r2 else 0 for i in range(N + 1)]
    assert ind_c == [1 if c1 <= j <= c2 else 0 for j in range(Mc + 1)]
    assert vert_first == [[x * t for t in rw] for rw in outer(ind_r, ind_c)]
    # 줄마다의 표시(행 구간 표시 x 열 표시)를 세로로 차분하면 바깥곱 표시판이 된다
    row_marks = [[x * t for t in rw] for rw in outer(ind_r, ww)]
    assert matmul(Linv(N + 1), row_marks) == Dm
    assert matvec(Linv(N + 1), ind_r) == uu
    assert [rw[:Mc] for rw in vert_first[:N]] == rect_add(N, Mc, [(r1, c1, r2, c2, x)])
    # 여러 직사각형을 한 판에 모아도 된다(선형성)
    ups = []
    for _ in range(random.randint(1, 5)):
        a1 = random.randint(0, N - 1); a2 = random.randint(a1, N - 1)
        b1 = random.randint(0, Mc - 1); b2 = random.randint(b1, Mc - 1)
        ups.append((a1, b1, a2, b2, random.randint(-5, 5)))
    brute = zeros(N, Mc)
    for a1, b1, a2, b2, y in ups:
        for i in range(a1, a2 + 1):
            for j in range(b1, b2 + 1):
                brute[i][j] += y
    assert rect_add(N, Mc, ups) == brute
    # 직사각형 합 = (e_{r2+1} - e_{r1})^T S (e_{c2+1} - e_{c1})
    A = [[random.randint(-9, 9) for _ in range(Mc)] for _ in range(N)]
    S = prefix2d(A)
    left = vsub(e(N + 1, r2 + 1), e(N + 1, r1))
    right = vsub(e(Mc + 1, c2 + 1), e(Mc + 1, c1))
    bil = sum(left[i] * S[i][j] * right[j] for i in range(N + 1) for j in range(Mc + 1))
    direct = sum(A[i][j] for i in range(r1, r2 + 1) for j in range(c1, c2 + 1))
    assert bil == rect_sum_four(S, r1, c1, r2, c2) == direct
    # 2차원 누적 합 S = L_행 A L_열^T (P[0]을 뗀 부분)
    assert [rw[1:] for rw in S[1:]] == matmul(matmul(L(N), A), transpose(L(Mc)))

# ---------- 6. XOR, 나머지 덧셈 ----------
for _ in range(TRIALS // 4):
    n = random.randint(1, 12)
    a = [random.randint(0, 255) for _ in range(n)]
    Px = [0]
    for v in a:
        Px.append(Px[-1] ^ v)
    l = random.randint(0, n - 1); r = random.randint(l, n - 1)
    acc = 0
    for v in a[l:r + 1]:
        acc ^= v
    assert Px[r + 1] ^ Px[l] == acc
    assert [Px[i + 1] ^ Px[i] for i in range(n)] == a
    # GF(2)에서 L^{-1}: -1 자리가 1인 두 대각 모양, L L^{-1} = I (mod 2)
    Linv2 = [[t % 2 for t in rw] for rw in Linv(n)]
    assert Linv2 == [[1 if j in (i, i - 1) else 0 for j in range(n)] for i in range(n)]
    assert [[t % 2 for t in rw] for rw in matmul(L(n), Linv2)] == eye(n)
    # 비트마다 보면 XOR 누적은 GF(2)에서 L을 곱하는 일이다
    for bit in range(8):
        bits = [(v >> bit) & 1 for v in a]
        assert [t % 2 for t in matvec(L(n), bits)] == [(q >> bit) & 1 for q in Px[1:]]
    # 나머지 덧셈
    m = random.randint(2, 50)
    am = [random.randint(0, m - 1) for _ in range(n)]
    Pm = [0]
    for v in am:
        Pm.append((Pm[-1] + v) % m)
    assert (Pm[r + 1] - Pm[l]) % m == sum(am[l:r + 1]) % m

# ---------- 7. 최솟값 반례(카드 C3) ----------
def prefix_min(a):
    out, cur = [], float("inf")
    for v in a:
        cur = min(cur, v)
        out.append(cur)
    return out


A1, B1 = [1, 5, 2], [1, 1, 2]
assert prefix_min(A1) == prefix_min(B1) == [1, 1, 1]
assert min(A1[1:3]) == 2 and min(B1[1:3]) == 1
# 무작위로도: 누적 최솟값이 같은데 구간 최솟값이 다른 쌍이 흔하다
found = 0
for _ in range(2000):
    s = [random.randint(1, 4) for _ in range(4)]
    t = [random.randint(1, 4) for _ in range(4)]
    if prefix_min(s) == prefix_min(t) and min(s[1:]) != min(t[1:]):
        found += 1
assert found > 0

# ---------- 8. 실수 반올림 반례 ----------
af = [1e16, 1.0, 1.0]
Pf = [0.0]
for v in af:
    Pf.append(Pf[-1] + v)
assert Pf[2] == 1e16 and Pf[3] == 1e16
assert Pf[3] - Pf[1] == 0.0
assert af[1] + af[2] == 2.0
# 차분해도 a[1], a[2]가 0으로 나온다: 원래 값으로 돌아오지 않는다
back = [Pf[i + 1] - Pf[i] for i in range(3)]
assert back == [1e16, 0.0, 0.0] and back != af

# ---------- 9. 전이 문제: 결합 누적분포 ----------
Q = [[Fr(10, 100), Fr(5, 100), Fr(5, 100)],
     [Fr(10, 100), Fr(20, 100), Fr(10, 100)],
     [Fr(5, 100), Fr(15, 100), Fr(20, 100)]]
assert sum(sum(rw) for rw in Q) == 1
F = [[Fr(10, 100), Fr(15, 100), Fr(20, 100)],
     [Fr(20, 100), Fr(45, 100), Fr(60, 100)],
     [Fr(25, 100), Fr(65, 100), Fr(100, 100)]]
# F(i, j) = Pr[X <= i, Y <= j] 정의대로
for i in range(3):
    for j in range(3):
        assert F[i][j] == sum(Q[s][t] for s in range(i + 1) for t in range(j + 1))
assert matmul(matmul(L(3), Q), transpose(L(3))) == F                 # F = L Q L^T
LiF = matmul(Linv(3), F)
assert LiF == [[Fr(10, 100), Fr(15, 100), Fr(20, 100)],
               [Fr(10, 100), Fr(30, 100), Fr(40, 100)],
               [Fr(5, 100), Fr(20, 100), Fr(40, 100)]]
for i in range(3):                                                   # Pr[X = i, Y <= j]
    for j in range(3):
        assert LiF[i][j] == sum(Q[i][t] for t in range(j + 1))
assert matmul(LiF, transpose(Linv(3))) == Q                          # Q = L^{-1} F L^{-T}
# (L^T)^{-1} = (L^{-1})^T
assert matmul(transpose(L(3)), transpose(Linv(3))) == eye(3)
assert matmul(transpose(Linv(3)), transpose(L(3))) == eye(3)
# 오른쪽에서 (L^{-1})^T가 하는 일: 칸마다 바로 왼쪽 칸을 뺀다
assert matmul(LiF, transpose(Linv(3))) == [[LiF[i][j] - (LiF[i][j - 1] if j > 0 else 0) for j in range(3)] for i in range(3)]
# 흔한 실수: 오른쪽에도 L^{-1}을 곱하면 칸마다 바로 오른쪽 칸을 빼서 Q가 아니다
wrong = matmul(LiF, Linv(3))
assert wrong == [[LiF[i][j] - (LiF[i][j + 1] if j < 2 else 0) for j in range(3)] for i in range(3)]
assert wrong != Q
# (2) Pr[2 <= X <= 3, 2 <= Y <= 3] (번호 1부터: 인덱스 1..2)
four = F[2][2] - F[0][2] - F[2][0] + F[0][0]
assert four == Fr(65, 100)
v = [-1, 0, 1]                                                       # e_3 - e_1 (1부터 센 번호)
assert sum(v[i] * F[i][j] * v[j] for i in range(3) for j in range(3)) == four
assert Q[1][1] + Q[1][2] + Q[2][1] + Q[2][2] == four
assert [F[2][2], F[0][2], F[2][0], F[0][0]] == [1, Fr(20, 100), Fr(25, 100), Fr(10, 100)]

# ---------- 10. 카드 C1 ----------
a = [2, 7, 1]
assert matvec(L(3), a) == [2, 9, 10]
assert matvec(Linv(3), [2, 9, 10]) == [2, 7, 1]
assert [9 - 2, 10 - 9] == [7, 1]
W = [[1, 0, 0], [-1, 1, 0], [-1, -1, 1]]                              # 흔한 오답: 아래를 모두 -1
assert matvec(W, [2, 9, 10]) == [2, 7, -1]
assert matmul(W, L(3)) != eye(3) and matmul(L(3), W) != eye(3)

# ---------- 11. 카드 C2: 네 모서리 부호 ----------
for r1, c1, r2, c2 in [(0, 0, 1, 1), (1, 2, 3, 4), (0, 1, 0, 1)]:
    uu = vsub(e(6, r1), e(6, r2 + 1))
    ww = vsub(e(6, c1), e(6, c2 + 1))
    O = outer(uu, ww)
    assert [O[r1][c1], O[r1][c2 + 1], O[r2 + 1][c1], O[r2 + 1][c2 + 1]] == [1, -1, -1, 1]

print("ALL CHECKS PASSED")
