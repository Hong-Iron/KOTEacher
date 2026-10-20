"""36.격자 회전 ↔ 선형변환 문서의 주장을 확인한다.

칸 번호는 0-based (r, c)이고, 격자는 행 n개, 열 m개다.
2 × 2 행렬은 열벡터 (r, c)에 왼쪽에서 곱한다.
"""
import math
import random
from fractions import Fraction


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ---------- 격자 연산 (코드 쪽) ----------
def flip_ud(a):            # 위아래 뒤집기 a[::-1]
    return [list(row) for row in a[::-1]]


def transpose(a):          # zip(*a)
    return [list(x) for x in zip(*a)]


def flip_lr(a):            # 각 행 뒤집기
    return [row[::-1] for row in a]


def cw(a):                 # zip(*a[::-1])
    return [list(x) for x in zip(*a[::-1])]


def ccw(a):                # list(zip(*a))[::-1]
    return [list(x) for x in list(zip(*a))[::-1]]


def cw_alt(a):             # 전치한 뒤 각 행 뒤집기
    return [list(row)[::-1] for row in zip(*a)]


def anti_transpose(a):     # 반대각선 거울
    return [list(r)[::-1] for r in zip(*a)][::-1]


def rand_grid(rng, n, m):
    return [[rng.randint(0, 99) for _ in range(m)] for _ in range(n)]


# ---------- 행렬 (수학 쪽) ----------
def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))]


def mpow(A, k):
    n = len(A)
    R = [[int(i == j) for j in range(n)] for i in range(n)]
    for _ in range(k):
        R = matmul(R, A)
    return R


def det2(A):
    return A[0][0] * A[1][1] - A[0][1] * A[1][0]


def tr(A):
    return [list(x) for x in zip(*A)]


def J(k):                  # 단위행렬의 행 순서를 거꾸로 한 행렬
    return [[int(j == k - 1 - i) for j in range(k)] for i in range(k)]


def apply(M, v):
    return (M[0][0] * v[0] + M[0][1] * v[1], M[1][0] * v[0] + M[1][1] * v[1])


I2 = [[1, 0], [0, 1]]
F = [[-1, 0], [0, 1]]       # 위아래 뒤집기의 선형 부분
T = [[0, 1], [1, 0]]        # 전치의 선형 부분
L = [[1, 0], [0, -1]]       # 좌우 뒤집기의 선형 부분
AT = [[0, -1], [-1, 0]]     # 반대각선 뒤집기의 선형 부분
RCW = [[0, 1], [-1, 0]]     # R_{-90°}
RCCW = [[0, -1], [1, 0]]    # R_{90°}
NEG = [[-1, 0], [0, -1]]    # R_{180°}


def rot_float(theta):
    c, s = math.cos(theta), math.sin(theta)
    return [[c, -s], [s, c]]


def refl_float(alpha):     # 거울선의 각이 alpha인 반사 S_alpha
    c, s = math.cos(2 * alpha), math.sin(2 * alpha)
    return [[c, s], [s, -c]]


def close(A, B, eps=1e-9):
    return all(abs(A[i][j] - B[i][j]) < eps for i in range(len(A)) for j in range(len(A[0])))


def main():
    rng = random.Random(36)

    # ---------- 1. 먼저 비교해 보기: 3 × 3 표 ----------
    a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    check(flip_ud(a) == [[7, 8, 9], [4, 5, 6], [1, 2, 3]], "표: 위아래 뒤집기")
    check(transpose(a) == [[1, 4, 7], [2, 5, 8], [3, 6, 9]], "표: 전치")
    check(cw(a) == [[7, 4, 1], [8, 5, 2], [9, 6, 3]], "표: 시계 방향")
    check(ccw(a) == [[3, 6, 9], [2, 5, 8], [1, 4, 7]], "표: 반시계 방향")
    check(cw(cw(cw(cw(a)))) == a, "표: 시계 방향 네 번")
    check(mpow(RCW, 4) == I2, "표: R^4 = I")
    # 표 오른쪽 칸: n = 3에서 행렬 + 평행이동이 값을 옮기는 자리와 같다
    table = [(flip_ud, F, (2, 0)), (transpose, T, (0, 0)), (cw, RCW, (0, 2)), (ccw, RCCW, (2, 0))]
    for op, M, b in table:
        out = op(a)
        for r in range(3):
            for c in range(3):
                x, y = apply(M, (r, c))
                check(out[x + b[0]][y + b[1]] == a[r][c], "표: 행렬 + 평행이동")

    # ---------- 2. 대응 관계: 칸 번호 식 (직사각형 n × m) ----------
    formulas = {
        "ud": (flip_ud, lambda r, c, n, m: (n - 1 - r, c)),
        "tr": (transpose, lambda r, c, n, m: (c, r)),
        "cw": (cw, lambda r, c, n, m: (c, n - 1 - r)),
        "ccw": (ccw, lambda r, c, n, m: (m - 1 - c, r)),
        "lr": (flip_lr, lambda r, c, n, m: (r, m - 1 - c)),
        "180": (lambda g: flip_lr(flip_ud(g)), lambda r, c, n, m: (n - 1 - r, m - 1 - c)),
        "anti": (anti_transpose, lambda r, c, n, m: (m - 1 - c, n - 1 - r)),
    }
    linear = {"ud": F, "tr": T, "cw": RCW, "ccw": RCCW, "lr": L, "180": NEG, "anti": AT}
    shift = {"ud": lambda n, m: (n - 1, 0), "tr": lambda n, m: (0, 0), "cw": lambda n, m: (0, n - 1),
             "ccw": lambda n, m: (m - 1, 0), "lr": lambda n, m: (0, m - 1),
             "180": lambda n, m: (n - 1, m - 1), "anti": lambda n, m: (m - 1, n - 1)}
    for _ in range(500):
        n, m = rng.randint(1, 7), rng.randint(1, 7)
        g = rand_grid(rng, n, m)
        for key, (op, f) in formulas.items():
            out = op(g)
            for r in range(n):
                for c in range(m):
                    x, y = f(r, c, n, m)
                    check(out[x][y] == g[r][c], f"칸 번호 식 {key}")
                    lx, ly = apply(linear[key], (r, c))
                    sx, sy = shift[key](n, m)
                    check((lx + sx, ly + sy) == (x, y), f"선형 부분 + 평행이동 {key}")
            # 평행이동 = 가장 작은 번호가 0이 되게 고른 값
            imgs = [apply(linear[key], (r, c)) for r in range(n) for c in range(m)]
            check((-min(p[0] for p in imgs), -min(p[1] for p in imgs)) == shift[key](n, m),
                  f"평행이동은 최솟값을 0으로 {key}")
        # 1부터 세어도 평행이동은 남는다: 시계 방향은 (r, c) → (c, n + 1 - r)
        out = cw(g)
        for r in range(1, n + 1):
            for c in range(1, m + 1):
                x, y = c, n + 1 - r
                check(out[x - 1][y - 1] == g[r - 1][c - 1], "1-based 시계 방향 식")
                lx, ly = apply(RCW, (r, c))
                check((x - lx, y - ly) == (0, n + 1) != (0, 0), "1-based에서도 평행이동 (0, n + 1)")
    # 반사 두 번 = 회전 (선형 부분의 곱)
    check(matmul(T, F) == RCW, "T·F = R_-90")
    check(matmul(F, T) == RCCW, "F·T = R_90")
    check(RCW == [[round(v) for v in row] for row in rot_float(-math.pi / 2)], "R_-90 성분")
    check(RCCW == [[round(v) for v in row] for row in rot_float(math.pi / 2)], "R_90 성분")
    check(matmul(F, L) == NEG and matmul(L, F) == NEG, "위아래·좌우 = 180°")
    check(matmul(F, F) == I2 and matmul(T, T) == I2, "같은 반사 두 번 = 제자리")

    # ---------- 3. 값의 행렬 A로 보기 (06) ----------
    for _ in range(500):
        n, m = rng.randint(1, 7), rng.randint(1, 7)
        A = rand_grid(rng, n, m)
        Jn, Jm = J(n), J(m)
        check(flip_ud(A) == matmul(Jn, A), "a[::-1] = J_n A")
        check(flip_lr(A) == matmul(A, Jm), "행마다 뒤집기 = A J_m")
        check(transpose(A) == tr(A), "zip(*a) = A^T")
        check(cw(A) == tr(matmul(Jn, A)) == matmul(tr(A), Jn), "cw = (J_n A)^T = A^T J_n")
        check(cw_alt(A) == cw(A), "전치한 뒤 각 행 뒤집기 = 시계 방향")
        check(ccw(A) == matmul(Jm, tr(A)) == tr(matmul(A, Jm)), "ccw = J_m A^T = (A J_m)^T")
        check(flip_lr(flip_ud(A)) == matmul(matmul(Jn, A), Jm), "180° = J_n A J_m")
        check(tr(Jn) == Jn and matmul(Jn, Jn) == [[int(i == j) for j in range(n)] for i in range(n)],
              "J는 대칭이고 J^2 = I")
        check(ccw(cw(A)) == A and cw(ccw(A)) == A, "반시계는 시계 방향을 되돌린다")
        B = matmul(tr(A), Jn)                     # 시계 방향으로 돌린 m × n 격자
        check(matmul(Jn, tr(B)) == matmul(matmul(Jn, Jn), A) == A, "J_n (A^T J_n)^T = J_n^2 A = A")
        check(ccw(B) == matmul(Jn, tr(B)), "m × n 격자의 반시계는 J_n B^T")
        check([list(row[::-1]) for row in zip(*A)] == cw(A), "[row[::-1] for row in zip(*a)] = 시계 방향")
        check(flip_ud(flip_ud(A)) == A and transpose(transpose(A)) == A, "반사는 두 번이면 제자리")
    # 06 C1의 B는 J_2: 왼쪽 곱은 행, 오른쪽 곱은 열을 바꾼다
    A2 = [[1, 2], [3, 4]]
    check(J(2) == [[0, 1], [1, 0]], "J_2 = 06 C1의 B")
    check(matmul(J(2), A2) == [[3, 4], [1, 2]] and matmul(A2, J(2)) == [[2, 1], [4, 3]], "06 C1")
    # 역의 순서: (TF)^-1 = F^-1 T^-1 = FT
    check(matmul(matmul(T, F), matmul(F, T)) == I2, "FT·TF = I")
    check(matmul(matmul(F, T), matmul(T, F)) == I2, "TF·FT = I")
    check(matmul(T, F) != matmul(F, T), "TF ≠ FT")

    # ---------- 4. 방향 (dr, dc): 평행이동이 지워진다 ----------
    d = (-1, 0)                                   # 위
    seq = []
    for _ in range(4):
        d = (d[1], -d[0])                         # 시계 방향 (dc, -dr)
        seq.append(d)
    check(seq == [(0, 1), (1, 0), (0, -1), (-1, 0)], "위 → 오른쪽 → 아래 → 왼쪽 → 위")
    for _ in range(300):
        n, m = rng.randint(1, 8), rng.randint(1, 8)
        r1, c1, r2, c2 = rng.randrange(n), rng.randrange(m), rng.randrange(n), rng.randrange(m)
        p = (c1, n - 1 - r1)
        q = (c2, n - 1 - r2)
        diff = (q[0] - p[0], q[1] - p[1])
        check(diff == apply(RCW, (r2 - r1, c2 - c1)), "차이는 선형 부분만 받는다")
        check(apply(RCW, (r2 - r1, c2 - c1)) == (c2 - c1, -(r2 - r1)), "(dr, dc) → (dc, -dr)")

    # ---------- 5. 어디까지 같은가 ----------
    # (a) 가운데를 원점으로 잡으면 평행이동이 사라진다
    for n in range(1, 7):
        for m in range(1, 7):
            for r in range(n):
                for c in range(m):
                    u = (Fraction(r) - Fraction(n - 1, 2), Fraction(c) - Fraction(m - 1, 2))
                    x, y = c, n - 1 - r                    # cw 뒤의 칸 (m × n 격자)
                    v = (Fraction(x) - Fraction(m - 1, 2), Fraction(y) - Fraction(n - 1, 2))
                    check(v == apply(RCW, u), "가운데 원점에서 cw = R_-90")
    # 3 × 3: (r - 1, c - 1)
    for r in range(3):
        for c in range(3):
            x, y = c, 2 - r
            check((x - 1, y - 1) == apply(RCW, (r - 1, c - 1)), "3 × 3 가운데 원점")
    # (b) 45°는 칸을 칸으로 보내지 않는다: 가운데에서 (0, 1) 떨어진 칸
    R45 = rot_float(math.pi / 4)
    v = (R45[0][0] * 0 + R45[0][1] * 1, R45[1][0] * 0 + R45[1][1] * 1)
    check(all(abs(2 * t - round(2 * t)) > 0.1 for t in v), "45°: 칸 가운데로 가지 않음")
    check(abs(abs(v[0]) - math.sqrt(2) / 2) < 1e-12 and abs(abs(v[1]) - math.sqrt(2) / 2) < 1e-12, "45°: 0.707")
    # (c) 직사각형: 모양을 지키는 대칭은 넷
    g = rand_grid(rng, 2, 3)
    keep = [k for k, (op, _) in formulas.items() if len(op(g)) == 2 and len(op(g)[0]) == 3]
    swap = [k for k, (op, _) in formulas.items() if len(op(g)) == 3 and len(op(g)[0]) == 2]
    check(sorted(keep) == sorted(["ud", "lr", "180"]), "2 × 3: 모양 유지 (그대로 제외)")
    check(sorted(swap) == sorted(["tr", "anti", "cw", "ccw"]), "2 × 3: 모양이 3 × 2로")
    # 시계 방향 네 번: 평행이동이 n - 1, m - 1로 번갈아 붙고 합치면 제자리
    for _ in range(200):
        n, m = rng.randint(1, 7), rng.randint(1, 7)
        g = rand_grid(rng, n, m)
        check(cw(cw(cw(cw(g)))) == g, "직사각형 cw 네 번 = 제자리")
        dims, h = [], g
        for _ in range(4):
            dims.append(len(h) - 1)               # 이번 단계의 평행이동 (행 수 - 1)
            h = cw(h)
        check(dims == [n - 1, m - 1, n - 1, m - 1], "평행이동이 번갈아 붙음")

    def H(k):                                     # 동차 좌표의 시계 방향 회전 (행 수 k)
        return [[0, 1, 0], [-1, 0, k - 1], [0, 0, 1]]
    I3 = [[int(i == j) for j in range(3)] for i in range(3)]
    for n in range(1, 8):
        check(mpow(H(n), 4) == I3, "정사각: H^4 = I")
        for m in range(1, 8):
            check(matmul(H(m), matmul(H(n), matmul(H(m), H(n)))) == I3, "직사각: 번갈아 곱하면 I")
            if n != m:
                check(matmul(H(n), H(n)) != matmul(H(m), H(n)), "직사각: 같은 함수의 제곱이 아님")
        for r in range(n):
            for c in range(n):
                out = matmul(H(n), [[r], [c], [1]])
                check([row[0] for row in out] == [c, n - 1 - r, 1], "H (r, c, 1) = (c, n - 1 - r, 1)")
    # (d) 길이가 다른 줄: zip은 짧은 줄에 맞춰 자른다
    check(list(zip(*[[1, 2, 3], [4, 5]])) == [(1, 4), (2, 5)], "들쭉날쭉한 리스트")
    # (e) (r, c) 좌표계 = 교과서 (x, y)를 90° 돌린 것: (r, c) = (-y, x)
    C = [[0, -1], [1, 0]]                         # (x, y) → (r, c)
    check(C == RCCW and det2(C) == 1, "(r, c) = R_90 (x, y)")
    Cinv = [[0, 1], [-1, 0]]
    check(matmul(C, Cinv) == I2, "C 역행렬")
    for M in [RCW, RCCW, F, T]:
        conj = matmul(Cinv, matmul(M, C))         # 같은 변환을 (x, y)로 적은 행렬
        check(det2(conj) == det2(M), "좌표계를 돌려도 행렬식 같음")
    check(matmul(Cinv, matmul(RCW, C)) == RCW, "시계 방향은 (x, y)에서도 R_-90")
    # 전치의 거울선: (r, c)에서 (1, 1) 방향 = 화면의 왼쪽 위 → 오른쪽 아래
    check(apply(T, (1, 1)) == (1, 1), "전치의 거울 방향 (1, 1)")
    r_, c_ = 1, 1
    x_, y_ = c_, -r_                               # 화면 좌표: 오른쪽 +x, 위 +y
    check(x_ > 0 and y_ < 0, "(1, 1)은 화면에서 오른쪽 아래")
    check(apply(matmul(Cinv, matmul(T, C)), (1, -1)) == (1, -1), "(x, y) 그림에서 거울은 y = -x")
    # (x, y) = (c, r)로 적으면 이름이 뒤바뀐다
    P = [[0, 1], [1, 0]]
    check(matmul(P, matmul(RCW, P)) == RCCW, "P R_-90 P = R_90")
    for M in [RCW, RCCW, F, T, L, AT, NEG, I2]:
        check(det2(matmul(P, matmul(M, P))) == det2(M), "순서를 바꿔도 행렬식 같음")

    # ---------- 6. 이 연결로 얻는 것 ----------
    # 8가지 대칭 = 부호 붙은 치환 행렬 8개, 행렬식 +1 넷과 -1 넷
    group = {tuple(map(tuple, I2))}
    frontier = [I2]
    while frontier:
        nxt = []
        for M in frontier:
            for G in (F, T):
                P2 = matmul(G, M)
                key = tuple(map(tuple, P2))
                if key not in group:
                    group.add(key)
                    nxt.append(P2)
        frontier = nxt
    check(len(group) == 8, "F와 T로 만든 대칭은 8개")
    signed_perm = set()
    for (i, j) in [(0, 1), (1, 0)]:
        for s1 in (1, -1):
            for s2 in (1, -1):
                M = [[0, 0], [0, 0]]
                M[0][i], M[1][j] = s1, s2
                signed_perm.add(tuple(map(tuple, M)))
    check(group == signed_perm, "8개 = 부호 붙은 치환 행렬")
    dets = sorted(det2([list(r) for r in M]) for M in group)
    check(dets == [-1] * 4 + [1] * 4, "행렬식 +1 넷, -1 넷")
    rot = {tuple(map(tuple, mpow(RCW, k))) for k in range(4)}
    check(rot == {tuple(map(tuple, M)) for M in [I2, RCW, NEG, RCCW]}, "회전 넷")
    check(all(det2([list(r) for r in M]) == 1 for M in rot), "회전의 행렬식 +1")
    check(all(det2(M) == -1 for M in [F, T, L, AT]), "반사의 행렬식 -1")
    # 회전을 몇 번 이어도 +1: 회전끼리의 곱은 회전 안에 머문다
    for M1 in rot:
        for M2 in rot:
            check(tuple(map(tuple, matmul([list(r) for r in M1], [list(r) for r in M2]))) in rot, "회전끼리 닫힘")
    # 자물쇠와 열쇠: 돌려서는 거울상 열쇠가 나오지 않는다
    key = [[1, 1, 0], [0, 1, 0], [0, 1, 1]]       # S자 모양
    rots, h = [], key
    for _ in range(4):
        h = cw(h)
        rots.append(h)
    check(flip_lr(key) not in rots, "S자 열쇠를 돌려서 Z자가 나오지 않음")
    # 돌려서 거울상이 나온다 ⇔ 열쇠가 네 거울 중 하나에 대해 대칭
    REFLS = [flip_ud, flip_lr, transpose, anti_transpose]

    def rotations(g):
        out, h = [], g
        for _ in range(4):
            h = cw(h)
            out.append(h)
        return out

    def mirror_symmetric(g):
        return any(S(g) == g for S in REFLS)

    n_sym = n_asym = 0
    for k in (1, 2, 3):
        for bits in range(2 ** (k * k)):
            g = [[(bits >> (r * k + c)) & 1 for c in range(k)] for r in range(k)]
            check((flip_lr(g) in rotations(g)) == mirror_symmetric(g), "거울상이 나옴 ⇔ 거울 대칭 (전수)")
            if mirror_symmetric(g):
                n_sym += 1
            else:
                n_asym += 1
    check(n_sym > 0 and n_asym > 0, "대칭·비대칭 열쇠가 모두 있음")
    for _ in range(2000):
        k = rng.randint(1, 5)
        g = [[rng.randint(0, 1) for _ in range(k)] for _ in range(k)]
        check((flip_lr(g) in rotations(g)) == mirror_symmetric(g), "거울상이 나옴 ⇔ 거울 대칭 (무작위)")
    diag_key = [[1, 1, 0], [1, 0, 0], [0, 0, 0]]
    check(transpose(diag_key) == diag_key, "예: 대각선 대칭 열쇠")
    check(flip_lr(diag_key) == cw(diag_key) and flip_lr(diag_key) != diag_key, "예: 좌우 뒤집기 = 시계 방향 한 번")
    # 반시계 = 시계 세 번 = 시계의 역: 네 방향의 집합이 같다 (직사각형도)
    check(mpow(RCW, 3) == RCCW and matmul(RCW, RCCW) == I2 and mpow(RCW, 2) == NEG, "R_90 = R_-90^3")
    for n in range(1, 7):
        for m in range(1, 7):
            for _ in range(15):
                g = rand_grid(rng, n, m)
                check(ccw(g) == cw(cw(cw(g))), "ccw = cw^3")
                s_cw, s_ccw, h1, h2 = [], [], g, g
                for _ in range(4):
                    h1, h2 = cw(h1), ccw(h2)
                    s_cw.append(h1)
                    s_ccw.append(h2)
                check(sorted(map(str, s_cw)) == sorted(map(str, s_ccw)), "네 방향 집합이 같음")
    # 반사 두 번 = 거울 사이 각의 두 배만큼 회전: S_a S_b = R_{2(a - b)}
    for _ in range(1000):
        al, be = rng.uniform(-4, 4), rng.uniform(-4, 4)
        check(close(matmul(refl_float(al), refl_float(be)), rot_float(2 * (al - be))), "S_a S_b = R_2(a-b)")
    deg = math.pi / 180
    rounded = lambda M: [[round(v) for v in row] for row in M]
    check(rounded(refl_float(90 * deg)) == F, "가로 거울 = 각 90°")
    check(rounded(refl_float(45 * deg)) == T, "대각선 거울 = 각 45°")
    check(rounded(refl_float(0)) == L, "세로 거울 = 각 0°")
    check(rounded(refl_float(-45 * deg)) == AT, "반대각선 거울 = 각 -45°")
    check(rounded(matmul(refl_float(45 * deg), refl_float(90 * deg))) == RCW, "가로 → 대각선: 시계 90°")
    check(rounded(matmul(refl_float(90 * deg), refl_float(0))) == NEG, "세로 → 가로: 180°")

    # ---------- 7. 전이 문제: 좌우 반전 뒤 시계 방향 ----------
    check(matmul(RCW, L) == AT, "선형 부분 R_-90 · diag(1, -1) = 반대각선 반사")
    check(matmul(AT, L) == RCW, "시계 방향 = 세로 거울 뒤 반대각선 거울")
    check(rounded(matmul(refl_float(-45 * deg), refl_float(0))) == RCW, "각 0° → -45°: 시계 90°")
    for _ in range(500):
        n, m = rng.randint(1, 7), rng.randint(1, 7)
        g = rand_grid(rng, n, m)
        out = cw(flip_lr(g))
        check(out == anti_transpose(g), "좌우 반전 뒤 시계 = 반대각선 뒤집기")
        check(len(out) == m and (m == 0 or len(out[0]) == n), "결과는 m × n")
        check(cw(g) == anti_transpose(flip_lr(g)), "cw = 좌우 반전 뒤 반대각선 뒤집기")
        check(flip_lr(flip_lr(g)) == g, "좌우 반전 두 번 = 제자리")
        check(anti_transpose(out) == g, "반대각선 뒤집기 두 번 = 제자리")
        check(flip_lr(ccw(out)) == g, "반시계 뒤 좌우 반전으로 되돌림")
    photo = [[1, 2, 3], [4, 5, 6]]
    edited = cw(flip_lr(photo))
    check(edited == [[6, 3], [5, 2], [4, 1]], "전이 문제 2 × 3 예")
    h, seen = edited, []
    for _ in range(4):
        h = cw(h)
        seen.append(h)
    check(photo not in seen, "회전만으로는 되돌릴 수 없음")
    check(tuple(map(tuple, AT)) not in rot, "반대각선 반사는 회전이 아님")
    # 회전만으로 되돌릴 수 있다 ⇔ 원래 사진이 거울 대칭 (직사각형 포함)
    for _ in range(4000):
        n, m = rng.randint(1, 4), rng.randint(1, 4)
        g = [[rng.randint(0, 1) for _ in range(m)] for _ in range(n)]
        check((g in rotations(cw(flip_lr(g)))) == mirror_symmetric(g), "회전으로 되돌림 ⇔ 거울 대칭 사진")
    sym_photo = [[1, 2, 1], [3, 4, 3]]            # 좌우 대칭
    check(flip_lr(sym_photo) == sym_photo, "좌우 대칭 사진")
    e = cw(flip_lr(sym_photo))
    check(ccw(e) == sym_photo and cw(cw(cw(e))) == sym_photo, "대칭 사진은 반시계 한 번(시계 세 번)으로 돌아옴")

    # ---------- 8. 확인 문제 ----------
    # C1: 순서를 바꾸면 역회전 (위 3절에서 FT·TF = I 확인)
    # C2: 위아래 뒤 좌우 = 180°
    g = [[1, 2], [3, 4]]
    check(flip_ud(g) == [[3, 4], [1, 2]], "C2 위아래")
    check(flip_lr(flip_ud(g)) == [[4, 3], [2, 1]], "C2 좌우")
    check(flip_lr(flip_ud(g)) == cw(cw(g)) and flip_lr(flip_ud(g)) != g, "C2 = 180°, 제자리 아님")
    check(det2(matmul(L, F)) == 1, "C2 행렬식 +1")
    # C3: 2 × 3 격자 반시계
    b = [[1, 2, 3], [4, 5, 6]]
    out = ccw(b)
    check(out == [[3, 6], [2, 5], [1, 4]], "C3 결과")
    check(list(zip(*b))[::-1] == [(3, 6), (2, 5), (1, 4)], "C3: 튜플 그대로의 출력")
    check(out[0][0] == 3 and out[2][1] == 4, "C3: 3은 (0, 0), 4는 (2, 1)")
    check(formulas["ccw"][1](0, 2, 2, 3) == (0, 0) and formulas["ccw"][1](1, 0, 2, 3) == (2, 1), "C3 식")
    wrong = 0
    for r in range(2):
        for c in range(3):
            x, y = 2 - 1 - c, r                   # 틀린 식 (n - 1 - c, r)
            if not (0 <= x < 3 and 0 <= y < 2) or out[x][y] != b[r][c]:
                wrong += 1
    check(wrong > 0, "C3: n - 1 - c는 직사각형에서 틀림")
    bad_total = 0
    for _ in range(300):
        n, m = rng.randint(1, 7), rng.randint(1, 7)
        if n == m:
            continue
        g = rand_grid(rng, n, m)
        o = ccw(g)
        for r in range(n):
            for c in range(m):
                x, y = n - 1 - c, r
                if not (0 <= x < m and 0 <= y < n) or o[x][y] != g[r][c]:
                    bad_total += 1
    check(bad_total > 0, "n - 1 - c 식은 직사각형에서 깨짐")

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
