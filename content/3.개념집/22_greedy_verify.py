"""22.그리디: 회의실 배정과 동전 거스름으로 문서의 주장을 확인한다."""
import random
from itertools import combinations


def pick_by(meetings, key):
    """key 순서로 보며, 앞서 고른 것과 겹치지 않으면 고른다. 끝나는 시각에 바로 시작해도 된다."""
    chosen = []
    for m in sorted(meetings, key=key):
        if all(m[1] <= c[0] or c[1] <= m[0] for c in chosen):
            chosen.append(m)
    return chosen


def by_end(meetings):
    chosen, end = [], float("-inf")
    for s, e in sorted(meetings, key=lambda m: m[1]):
        if s >= end:
            chosen.append((s, e))
            end = e
    return chosen


def brute(meetings):
    for r in range(len(meetings), 0, -1):
        for comb in combinations(meetings, r):
            c = sorted(comb, key=lambda m: m[0])
            if all(a[1] <= b[0] for a, b in zip(c, c[1:])):
                return r
    return 0


def coins_greedy(coins, amount):
    cnt = 0
    for c in sorted(coins, reverse=True):
        cnt += amount // c
        amount %= c
    return cnt if amount == 0 else None


def coins_dp(coins, amount):
    INF = float("inf")
    best = [0] + [INF] * amount
    for x in range(1, amount + 1):
        for c in coins:
            if c <= x and best[x - c] + 1 < best[x]:
                best[x] = best[x - c] + 1
    return best[amount]


if __name__ == "__main__":
    # 예시로 보기: 회의 8개
    M = {"A": (1, 4), "B": (3, 5), "C": (0, 6), "D": (5, 7), "E": (3, 8), "F": (5, 9), "G": (6, 10), "H": (8, 11)}
    got = by_end(list(M.values()))
    assert got == [M["A"], M["D"], M["H"]] and brute(list(M.values())) == 3
    # 다른 기준의 반례
    ex1 = [(0, 10), (1, 2), (3, 4)]
    assert len(pick_by(ex1, key=lambda m: m[0])) == 1 and brute(ex1) == 2
    ex2 = [(0, 5), (4, 6), (5, 10)]
    assert len(pick_by(ex2, key=lambda m: m[1] - m[0])) == 1 and brute(ex2) == 2
    # C3: 겹치는 회의가 가장 적은 것부터 고르기도 틀린다
    ex3 = [(0, 2), (1, 3), (1, 3), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7), (5, 7), (5, 7), (6, 8)]
    overlaps = lambda m: sum(1 for o in ex3 if o is not m and o[0] < m[1] and m[0] < o[1])
    assert len(pick_by(ex3, key=overlaps)) == 3 and brute(ex3) == 4 == len(by_end(ex3))
    # 무작위: 끝나는 시각 순 그리디 = 모든 조합을 보는 방법
    rng = random.Random(22)
    for _ in range(1500):
        ms = []
        for _ in range(rng.randint(1, 9)):
            s = rng.randint(0, 15)
            ms.append((s, s + rng.randint(1, 6)))
        assert len(by_end(ms)) == brute(ms), ms
    # 동전: 1, 3, 4원으로 6원
    assert coins_greedy([1, 3, 4], 6) == 3 and coins_dp([1, 3, 4], 6) == 2
    # 우리나라 동전 10, 50, 100, 500원은 1만 원까지 그리디가 늘 최소
    kr = [10, 50, 100, 500]
    best = [0] + [float("inf")] * 10000
    for x in range(1, 10001):
        for c in kr:
            if c <= x and best[x - c] + 1 < best[x]:
                best[x] = best[x - c] + 1
    assert all(coins_greedy(kr, a) == best[a] for a in range(10, 10001, 10))
    print("ALL CHECKS PASSED")
