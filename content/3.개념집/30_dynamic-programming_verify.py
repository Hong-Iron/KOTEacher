"""30.동적 계획법: 문서와 예제 사다리의 예시를 느린 방법과 비교해 확인한다."""
import random
import sys
from functools import lru_cache
from itertools import combinations, product


# 피보나치: 그대로 재귀 vs 기억하기
def fib_calls(n):
    cnt = [0]

    def f(k):
        cnt[0] += 1
        return k if k < 2 else f(k - 1) + f(k - 2)

    return f(n), cnt[0]


def fib_memo_calls(n):
    cnt, miss = [0], [0]
    memo = {}

    def f(k):
        cnt[0] += 1
        if k in memo:
            return memo[k]
        miss[0] += 1
        memo[k] = k if k < 2 else f(k - 1) + f(k - 2)
        return memo[k]

    return f(n), cnt[0], miss[0]


# 동전 최소 개수
def coin_dp(coins, x):
    INF = float("inf")
    dp = [0] + [INF] * x
    for v in range(1, x + 1):
        for c in coins:
            if c <= v and dp[v - c] + 1 < dp[v]:
                dp[v] = dp[v - c] + 1
    return dp


def coin_brute(coins, x):
    for k in range(0, x + 1):
        for combo in product(coins, repeat=k):
            if sum(combo) == x:
                return k
    return float("inf")


def coin_greedy(coins, x):
    cnt = 0
    for c in sorted(coins, reverse=True):
        cnt += x // c
        x %= c
    return cnt if x == 0 else None


# 사다리 1: 계단
def stairs(n):
    dp = [1, 1] + [0] * max(0, n - 1)
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]


def stairs_brute(n):
    return sum(1 for k in range(n + 1) for steps in product((1, 2), repeat=k) if sum(steps) == n)


# 사다리 2: 격자 최소 비용
def grid_min(g):
    R, C = len(g), len(g[0])
    dp = [[0] * C for _ in range(R)]
    for r in range(R):
        for c in range(C):
            if r == 0 and c == 0:
                dp[r][c] = g[0][0]
            elif r == 0:
                dp[r][c] = dp[r][c - 1] + g[r][c]
            elif c == 0:
                dp[r][c] = dp[r - 1][c] + g[r][c]
            else:
                dp[r][c] = min(dp[r - 1][c], dp[r][c - 1]) + g[r][c]
    return dp


def grid_brute(g):
    R, C = len(g), len(g[0])
    best = float("inf")
    for downs in combinations(range(R + C - 2), R - 1):
        r = c = 0
        s = g[0][0]
        for step in range(R + C - 2):
            if step in downs:
                r += 1
            else:
                c += 1
            s += g[r][c]
        best = min(best, s)
    return best


# 사다리 3: 0-1 배낭
def knapsack(items, W):
    dp = [0] * (W + 1)
    for w, v in items:
        for cap in range(W, w - 1, -1):          # 큰 쪽부터: 같은 물건을 두 번 쓰지 않게
            dp[cap] = max(dp[cap], dp[cap - w] + v)
    return dp[W]


def knapsack_forward(items, W):
    dp = [0] * (W + 1)
    for w, v in items:
        for cap in range(w, W + 1):              # 작은 쪽부터: 같은 물건을 여러 번 쓰게 된다
            dp[cap] = max(dp[cap], dp[cap - w] + v)
    return dp[W]


def knapsack_brute(items, W):
    best = 0
    for k in range(len(items) + 1):
        for comb in combinations(items, k):
            if sum(w for w, _ in comb) <= W:
                best = max(best, sum(v for _, v in comb))
    return best


# 사다리 4: 가장 긴 증가하는 부분 수열
def lis(a):
    dp = [1] * len(a)
    for i in range(len(a)):
        for j in range(i):
            if a[j] < a[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp, default=0), dp


def lis_brute(a):
    for k in range(len(a), 0, -1):
        for comb in combinations(a, k):
            if all(x < y for x, y in zip(comb, comb[1:])):
                return k
    return 0


if __name__ == "__main__":
    # 피보나치
    assert fib_calls(30) == (832040, 2_692_537)
    assert fib_memo_calls(30) == (832040, 59, 31)
    # 동전 [1, 3, 4]
    assert coin_dp([1, 3, 4], 6) == [0, 1, 2, 1, 1, 2, 2]
    assert coin_greedy([1, 3, 4], 6) == 3
    # C1: 동전 [1, 5, 6, 9], 11원
    assert coin_dp([1, 5, 6, 9], 11)[11] == 2 and coin_greedy([1, 5, 6, 9], 11) == 3
    # 오해: 겹치는 부분 문제가 없으면 기억해도 호출 수가 같다(반으로 나눠 더하기)
    calls = {"plain": 0, "memo": 0}

    def half_sum(a, lo, hi, key):
        calls[key] += 1
        if hi - lo == 1:
            return a[lo]
        m = (lo + hi) // 2
        return half_sum(a, lo, m, key) + half_sum(a, m, hi, key)

    memo = {}

    def half_sum_memo(a, lo, hi):
        calls["memo"] += 1
        if (lo, hi) in memo:
            return memo[(lo, hi)]
        if hi - lo == 1:
            memo[(lo, hi)] = a[lo]
        else:
            m = (lo + hi) // 2
            memo[(lo, hi)] = half_sum_memo(a, lo, m) + half_sum_memo(a, m, hi)
        return memo[(lo, hi)]

    arr = list(range(64))
    assert half_sum(arr, 0, 64, "plain") == half_sum_memo(arr, 0, 64) == sum(arr)
    assert calls["plain"] == calls["memo"] == 127
    # 위에서부터(재귀+기억)는 n이 크면 재귀 한도에 걸린다
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)

    @lru_cache(maxsize=None)
    def ways(n):
        return 1 if n < 2 else ways(n - 1) + ways(n - 2)

    try:
        ways(5000)
        raise AssertionError("RecursionError가 나야 한다")
    except RecursionError:
        pass
    sys.setrecursionlimit(old)
    assert stairs(5000) > 0
    # 사다리 네 문제
    assert stairs(5) == 8 == stairs_brute(5)
    g2 = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
    assert grid_min(g2) == [[1, 4, 5], [2, 7, 6], [6, 8, 7]] and grid_brute(g2) == 7
    items = [(2, 3), (3, 4), (4, 5), (5, 6)]
    assert knapsack(items, 5) == 7 == knapsack_brute(items, 5)
    assert knapsack_forward([(2, 3)], 4) == 6 and knapsack([(2, 3)], 4) == 3
    a4 = [10, 9, 2, 5, 3, 7, 101, 18]
    assert lis(a4) == (4, [1, 1, 1, 2, 2, 3, 4, 4]) and lis_brute(a4) == 4
    # 무작위 비교
    rng = random.Random(30)
    for _ in range(300):
        coins = sorted(set(rng.randint(1, 7) for _ in range(rng.randint(1, 3))))
        x = rng.randint(0, 12)
        assert coin_dp(coins, x)[x] == coin_brute(coins, x)
        n = rng.randint(1, 12)
        assert stairs(n) == stairs_brute(n)
        R, C = rng.randint(1, 4), rng.randint(1, 4)
        g = [[rng.randint(0, 9) for _ in range(C)] for _ in range(R)]
        assert grid_min(g)[-1][-1] == grid_brute(g)
        its = [(rng.randint(1, 5), rng.randint(1, 9)) for _ in range(rng.randint(0, 6))]
        W = rng.randint(0, 10)
        assert knapsack(its, W) == knapsack_brute(its, W)
        a = [rng.randint(0, 9) for _ in range(rng.randint(0, 9))]
        assert lis(a)[0] == lis_brute(a)
    print("ALL CHECKS PASSED")
