"""단어 퍼즐 (프로그래머스 12983) 풀이와 검증."""
import random
import time
from collections import deque


def solution(strs, t):
    pieces = set(strs)
    INF = float("inf")
    dp = [0] + [INF] * len(t)                 # dp[i]: t의 앞 i글자를 만드는 최소 조각 수
    for i in range(1, len(t) + 1):
        for L in range(1, 6):                 # 조각 길이는 1 ~ 5
            if L <= i and dp[i - L] + 1 < dp[i] and t[i - L:i] in pieces:
                dp[i] = dp[i - L] + 1
    return dp[len(t)] if dp[len(t)] != INF else -1


def by_bfs(strs, t):
    """위치를 점으로, 조각 하나를 간선으로 보고 BFS로 가장 적은 조각 수를 찾는다."""
    n = len(t)
    dist = [-1] * (n + 1)
    dist[0] = 0
    q = deque([0])
    while q:
        i = q.popleft()
        for s in strs:
            j = i + len(s)
            if j <= n and dist[j] == -1 and t.startswith(s, i):
                dist[j] = dist[i] + 1
                q.append(j)
    return dist[n]


if __name__ == "__main__":
    assert solution(["ba", "na", "n", "a"], "banana") == 3
    assert solution(["app", "ap", "p", "l", "e", "ple", "pp"], "apple") == 2
    assert solution(["ba", "an", "nan", "ban", "n"], "banana") == -1
    assert solution(["ban", "ba", "nana"], "banana") == 2            # 긴 조각부터 붙이면 ban 뒤에 막힌다
    assert not any("banana"[3:].startswith(x) for x in ["ban", "ba", "nana"])
    # 6단계 추적: apple의 dp
    t = "apple"
    pieces = {"app", "ap", "p", "l", "e", "ple", "pp"}
    INF = float("inf")
    dp = [0] + [INF] * 5
    for i in range(1, 6):
        for L in range(1, 6):
            if L <= i and t[i - L:i] in pieces:
                dp[i] = min(dp[i], dp[i - L] + 1)
    assert dp == [0, INF, 1, 1, 2, 2]
    rng = random.Random(12983)
    for _ in range(3000):
        strs = list({"".join(rng.choice("ab") for _ in range(rng.randint(1, 5))) for _ in range(rng.randint(1, 6))})
        t = "".join(rng.choice("ab") for _ in range(rng.randint(1, 15)))
        assert solution(strs, t) == by_bfs(strs, t), (strs, t)
    strs = list({"".join(rng.choice("abc") for _ in range(rng.randint(1, 5))) for _ in range(100)})
    t = "".join(rng.choice("abc") for _ in range(20_000))
    t0 = time.perf_counter()
    solution(strs, t)
    tt = time.perf_counter() - t0
    assert tt < 10, tt
    print(f"t length 20000: {tt:.2f}s")
    print("ALL CHECKS PASSED")
