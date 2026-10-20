"""19.누적 합과 차분 배열: 문서의 예시와 공식을 확인한다."""
import random
from itertools import accumulate


def prefix(a):
    P = [0] * (len(a) + 1)
    for i, x in enumerate(a):
        P[i + 1] = P[i] + x
    return P


def range_add(n, updates):
    """updates: (l, r, x) — a[l..r]에 x를 더한다. 차분 배열로 처리한다."""
    D = [0] * (n + 1)
    for l, r, x in updates:
        D[l] += x
        D[r + 1] -= x
    return list(accumulate(D[:n]))


def count_sum_s(a, S):
    """합이 S인 연속 구간 수: 누적 합 P[j] - P[i] = S인 쌍을 딕셔너리로 센다(음수 있어도 된다)."""
    seen, run, cnt = {0: 1}, 0, 0
    for x in a:
        run += x
        cnt += seen.get(run - S, 0)
        seen[run] = seen.get(run, 0) + 1
    return cnt


def prefix2d(a):
    n, m = len(a), len(a[0])
    S = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            S[i + 1][j + 1] = a[i][j] + S[i][j + 1] + S[i + 1][j] - S[i][j]
    return S


def rect_sum(S, r1, c1, r2, c2):
    return S[r2 + 1][c2 + 1] - S[r1][c2 + 1] - S[r2 + 1][c1] + S[r1][c1]


def rect_add(n, m, updates):
    """updates: (r1, c1, r2, c2, x). 2차원 차분: 모서리 네 곳에 적고 두 방향으로 누적한다."""
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for r1, c1, r2, c2, x in updates:
        D[r1][c1] += x
        D[r1][c2 + 1] -= x
        D[r2 + 1][c1] -= x
        D[r2 + 1][c2 + 1] += x
    for i in range(n + 1):                 # 가로로 누적
        for j in range(1, m + 1):
            D[i][j] += D[i][j - 1]
    for j in range(m + 1):                 # 세로로 누적
        for i in range(1, n + 1):
            D[i][j] += D[i - 1][j]
    return [row[:m] for row in D[:n]]


if __name__ == "__main__":
    # 예시로 보기
    a = [3, 1, 4, 1, 5, 9]
    P = prefix(a)
    assert P == [0, 3, 4, 8, 9, 14, 23]
    assert P[5] - P[2] == 10 == sum(a[2:5])
    assert list(accumulate(a, initial=0)) == P
    # 차분 예시
    assert range_add(6, [(1, 3, 2), (2, 5, 5)]) == [0, 2, 7, 7, 5, 5]
    D = [0] * 7
    D[1] += 2; D[4] -= 2; D[2] += 5; D[6] -= 5
    assert D == [0, 2, 5, 0, -2, 0, -5]
    # 2차원 차분 예시: 3×3에서 (0,0)~(1,1)에 1
    assert rect_add(3, 3, [(0, 0, 1, 1, 1)]) == [[1, 1, 0], [1, 1, 0], [0, 0, 0]]
    M = [[0] * 4 for _ in range(4)]
    M[0][0] += 1; M[0][2] -= 1; M[2][0] -= 1; M[2][2] += 1
    assert [r[:3] for r in M[:3]] == [[1, 0, -1], [0, 0, 0], [-1, 0, 1]]
    M = [list(accumulate(r)) for r in M]
    assert [r[:3] for r in M[:3]] == [[1, 1, 0], [0, 0, 0], [-1, -1, 0]]
    M = [list(c) for c in zip(*[list(accumulate(col)) for col in zip(*M)])]
    assert [r[:3] for r in M[:3]] == [[1, 1, 0], [1, 1, 0], [0, 0, 0]]
    assert count_sum_s([4, -2, 1], 3) == 1
    # C1
    P1 = prefix([2, 7, 1, 8, 2, 8])
    assert P1 == [0, 2, 9, 10, 18, 20, 28] and P1[4] - P1[1] == 16
    # 무작위: 구간 합, 구간 더하기, 2차원 두 가지를 직접 계산과 비교
    rng = random.Random(19)
    for _ in range(2000):
        n = rng.randint(1, 15)
        a = [rng.randint(-9, 9) for _ in range(n)]
        P = prefix(a)
        l = rng.randrange(n); r = rng.randrange(l, n)
        assert P[r + 1] - P[l] == sum(a[l:r + 1])
        S0 = rng.randint(-5, 5)
        assert count_sum_s(a, S0) == sum(1 for i in range(n) for j in range(i, n) if sum(a[i:j + 1]) == S0)
        ups = []
        for _ in range(rng.randint(0, 6)):
            l = rng.randrange(n); r = rng.randrange(l, n)
            ups.append((l, r, rng.randint(-5, 5)))
        want = [0] * n
        for l, r, x in ups:
            for i in range(l, r + 1):
                want[i] += x
        assert range_add(n, ups) == want
        R, C = rng.randint(1, 6), rng.randint(1, 6)
        g = [[rng.randint(-9, 9) for _ in range(C)] for _ in range(R)]
        S = prefix2d(g)
        r1 = rng.randrange(R); r2 = rng.randrange(r1, R); c1 = rng.randrange(C); c2 = rng.randrange(c1, C)
        assert rect_sum(S, r1, c1, r2, c2) == sum(g[i][j] for i in range(r1, r2 + 1) for j in range(c1, c2 + 1))
        ups2 = []
        for _ in range(rng.randint(0, 5)):
            r1 = rng.randrange(R); r2 = rng.randrange(r1, R); c1 = rng.randrange(C); c2 = rng.randrange(c1, C)
            ups2.append((r1, c1, r2, c2, rng.randint(-5, 5)))
        want2 = [[0] * C for _ in range(R)]
        for r1, c1, r2, c2, x in ups2:
            for i in range(r1, r2 + 1):
                for j in range(c1, c2 + 1):
                    want2[i][j] += x
        assert rect_add(R, C, ups2) == want2
    print("ALL CHECKS PASSED")
