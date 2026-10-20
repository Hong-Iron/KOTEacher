"""31.구간 DP: 행렬 곱셈 순서 문제로 표와 주장을 확인한다."""
import random
from functools import lru_cache


def matrix_chain(dims):
    """행렬 A1 … Ak, Ai는 dims[i-1] × dims[i]. 곱셈 횟수의 최솟값과 표."""
    k = len(dims) - 1
    INF = float("inf")
    dp = [[0] * (k + 1) for _ in range(k + 1)]
    for length in range(2, k + 1):                    # 짧은 구간부터
        for i in range(1, k - length + 2):
            j = i + length - 1
            dp[i][j] = INF
            for m in range(i, j):                     # 마지막 곱셈의 자리
                cost = dp[i][m] + dp[m + 1][j] + dims[i - 1] * dims[m] * dims[j]
                if cost < dp[i][j]:
                    dp[i][j] = cost
    return dp[1][k], dp


def brute(dims):
    """괄호 치는 방법을 모두 재귀로 만든다."""
    @lru_cache(maxsize=None)
    def all_costs(i, j):
        if i == j:
            return frozenset([0])
        out = set()
        for m in range(i, j):
            for a in all_costs(i, m):
                for b in all_costs(m + 1, j):
                    out.add(a + b + dims[i - 1] * dims[m] * dims[j])
        return frozenset(out)
    return min(all_costs(1, len(dims) - 1))


def left_to_right(dims):
    cost, r = 0, dims[0]
    for i in range(1, len(dims) - 1):
        cost += r * dims[i] * dims[i + 1]
    return cost


def cheapest_first(dims):
    """그리디: 지금 이웃한 두 행렬의 곱 중 가장 싼 것부터 한다."""
    d = list(dims)
    cost = 0
    while len(d) > 2:
        i = min(range(1, len(d) - 1), key=lambda t: d[t - 1] * d[t] * d[t + 1])
        cost += d[i - 1] * d[i] * d[i + 1]
        del d[i]
    return cost


if __name__ == "__main__":
    # 예시로 보기: 10×30, 30×5, 5×60
    best, dp = matrix_chain([10, 30, 5, 60])
    assert best == 4500
    assert 10 * 30 * 5 + 10 * 5 * 60 == 4500 and 30 * 5 * 60 + 10 * 30 * 60 == 27000
    assert (dp[1][2], dp[2][3], dp[1][3]) == (1500, 9000, 4500)
    # C1: 5×10, 10×3, 3×12, 12×5
    b1, d1 = matrix_chain([5, 10, 3, 12, 5])
    assert b1 == 405 and (d1[1][2], d1[2][3], d1[3][4], d1[1][3], d1[2][4]) == (150, 360, 180, 330, 330)
    # C3: 가장 싼 곱셈부터 하는 그리디가 틀리는 예
    g = [1, 1, 3, 2]                                  # A 1×1, B 1×3, C 3×2
    assert (1 * 1 * 3, 1 * 3 * 2) == (3, 6)           # 먼저 할 수 있는 두 곱셈의 비용, AB가 더 싸다
    assert cheapest_first(g) == 9 and matrix_chain(g)[0] == 8
    assert sum((100 - L + 1) * (L - 1) for L in range(2, 101)) == 166_650    # n = 100의 나누는 자리 수 합
    # 무작위: 표 = 모든 괄호 치기
    rng = random.Random(31)
    for _ in range(1500):
        dims = [rng.randint(1, 20) for _ in range(rng.randint(2, 7))]
        assert matrix_chain(dims)[0] == brute(dims)
        assert matrix_chain(dims)[0] <= left_to_right(dims)
    print("ALL CHECKS PASSED")
