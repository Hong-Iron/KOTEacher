"""노란불 신호등 (프로그래머스 468371) 풀이와 검증."""
import random
from itertools import combinations_with_replacement
from math import lcm


def solution(signals):
    period = 1
    for g, y, r in signals:
        period = lcm(period, g + y + r)
    for t in range(1, period + 1):
        if all(g <= (t - 1) % (g + y + r) < g + y for g, y, r in signals):
            return t
    return -1


def slow(signals):
    """색을 한 칸씩 바꿔 가며 따라간다. 멈추는 곳은 주기들의 곱."""
    state = [[0, s[0]] for s in signals]        # [색 번호(0초록 1노랑 2빨강), 그 색의 남은 초]
    limit = 1
    for g, y, r in signals:
        limit *= g + y + r
    for t in range(1, limit + 1):
        if all(c == 1 for c, _ in state):
            return t
        for i, (g, y, r) in enumerate(signals):
            state[i][1] -= 1
            if state[i][1] == 0:
                state[i][0] = (state[i][0] + 1) % 3
                state[i][1] = (g, y, r)[state[i][0]]
    return -1


if __name__ == "__main__":
    assert solution([[2, 1, 2], [5, 1, 1]]) == 13
    assert solution([[2, 3, 2], [3, 1, 3], [2, 1, 1]]) == 11
    assert solution([[3, 3, 3], [5, 4, 2], [2, 1, 2]]) == 193
    assert solution([[1, 1, 4], [2, 1, 3], [3, 1, 2], [4, 1, 1]]) == -1
    assert solution([[1, 1, 1], [2, 1, 1]]) == 11
    rng = random.Random(468371)
    for _ in range(2000):
        n = rng.randint(2, 3)
        sig = []
        for _ in range(n):
            g, y = rng.randint(1, 5), rng.randint(1, 4)
            r = rng.randint(1, 5)
            sig.append([g, y, r])
        assert solution(sig) == slow(sig), sig
    best = max(lcm(*c) for c in combinations_with_replacement(range(3, 21), 5))
    assert best == 1007760, best
    import time
    t0 = time.perf_counter()
    assert solution([[14, 1, 1], [13, 1, 1], [11, 1, 1], [15, 1, 1], [17, 1, 1]]) == 1007759
    assert time.perf_counter() - t0 < 2.0
    print("ALL CHECKS PASSED")
