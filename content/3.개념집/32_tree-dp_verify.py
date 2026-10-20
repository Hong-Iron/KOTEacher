"""32.트리 DP: 이웃하지 않게 고른 칸의 값 합 최대(트리)로 표와 주장을 확인한다."""
import random
from itertools import combinations


def best_independent(n, parent, value):
    """점 1 ~ n, parent[v]: 부모(뿌리는 0). dp[v] = (v를 안 고른 최대, v를 고른 최대)."""
    children = [[] for _ in range(n + 1)]
    for v in range(2, n + 1):
        children[parent[v]].append(v)
    order, stack = [], [1]
    while stack:                                  # 뿌리부터 내려가는 순서를 적고
        v = stack.pop()
        order.append(v)
        stack.extend(children[v])
    dp = [(0, 0)] * (n + 1)
    for v in reversed(order):                     # 거꾸로 돌면 자식이 늘 먼저 계산된다
        skip = sum(max(dp[c]) for c in children[v])
        take = value[v] + sum(dp[c][0] for c in children[v])
        dp[v] = (skip, take)
    return max(dp[1]), dp


def brute(n, parent, value):
    best = 0
    for k in range(n + 1):
        for comb in combinations(range(1, n + 1), k):
            s = set(comb)
            if all(not (v in s and parent[v] in s) for v in range(2, n + 1)):
                best = max(best, sum(value[v] for v in comb))
    return best


def by_levels(n, parent, value):
    """그리디 흉내: 짝수 층 전부와 홀수 층 전부 중 큰 쪽."""
    depth = [0] * (n + 1)
    for v in range(2, n + 1):
        depth[v] = depth[parent[v]] + 1
    even = sum(value[v] for v in range(1, n + 1) if depth[v] % 2 == 0)
    odd = sum(value[v] for v in range(1, n + 1) if depth[v] % 2 == 1)
    return max(even, odd)


if __name__ == "__main__":
    # 예시로 보기: 1(5) - 2(3), 3(4); 2 - 4(6), 5(2); 3 - 6(1)
    parent = [0, 0, 1, 1, 2, 2, 3]
    value = [0, 5, 3, 4, 6, 2, 1]
    best, dp = best_independent(6, parent, value)
    assert best == 14 == brute(6, parent, value)
    assert dp[4] == (0, 6) and dp[5] == (0, 2) and dp[6] == (0, 1)
    assert dp[2] == (8, 3) and dp[3] == (1, 4) and dp[1] == (12, 14)
    # C1: 칸 4의 값을 1로
    v1 = [0, 5, 3, 4, 1, 2, 1]
    b1, d1 = best_independent(6, parent, v1)
    assert d1[2] == (3, 3) and d1[3] == (1, 4) and d1[1] == (7, 9) and b1 == 9 == brute(6, parent, v1)
    # C3: 한 줄 10 - 1 - 1 - 10에서 층 나누기가 틀린다
    p4, v4 = [0, 0, 1, 2, 3], [0, 10, 1, 1, 10]
    assert by_levels(4, p4, v4) == 11 and best_independent(4, p4, v4)[0] == 20 == brute(4, p4, v4)
    # 무작위 비교
    rng = random.Random(32)
    for _ in range(1500):
        n = rng.randint(1, 10)
        par = [0, 0] + [rng.randint(1, v - 1) for v in range(2, n + 1)]
        val = [0] + [rng.randint(0, 9) for _ in range(n)]
        assert best_independent(n, par, val)[0] == brute(n, par, val)
    # 한 줄로 이어진 30만 칸도 반복문이라 재귀 한도와 상관없다
    n = 300_000
    par = [0, 0] + list(range(1, n))
    val = [0] + [1] * n
    assert best_independent(n, par, val)[0] == 150_000
    print("ALL CHECKS PASSED")
