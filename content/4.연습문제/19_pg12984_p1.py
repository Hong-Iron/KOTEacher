"""지형 편집 (프로그래머스 12984) 풀이와 검증."""
import random
import time
from bisect import bisect_left


def solution(land, P, Q):
    h = sorted(x for row in land for x in row)
    n = len(h)
    S = [0]
    for x in h:
        S.append(S[-1] + x)                 # S[i]: 낮은 쪽 i칸의 높이 합
    best = None
    for i, t in enumerate(h):               # 목표 높이 후보: 지금 있는 높이들
        if i > 0 and h[i - 1] == t:
            continue
        k = bisect_left(h, t)               # t보다 낮은 칸 수
        add = t * k - S[k]                  # 낮은 칸을 t까지 채우는 블록 수
        remove = (S[n] - S[k]) - t * (n - k)   # 높은 칸을 t까지 깎는 블록 수
        cost = add * P + remove * Q
        if best is None or cost < best:
            best = cost
    return best


def by_every_height(land, P, Q):
    cells = [x for row in land for x in row]
    best = None
    for t in range(min(cells), max(cells) + 1):
        cost = sum((t - x) * P if x < t else (x - t) * Q for x in cells)
        best = cost if best is None else min(best, cost)
    return best


if __name__ == "__main__":
    assert solution([[1, 2], [2, 3]], 3, 2) == 5 == by_every_height([[1, 2], [2, 3]], 3, 2)
    assert solution([[4, 4, 3], [3, 2, 2], [2, 1, 0]], 5, 3) == 33
    # 6단계 추적: 예시 2의 높이 후보별 비용
    land = [[4, 4, 3], [3, 2, 2], [2, 1, 0]]
    cells = sorted(x for r in land for x in r)
    assert cells == [0, 1, 2, 2, 2, 3, 3, 4, 4]
    costs = {t: sum((t - x) * 5 if x < t else (x - t) * 3 for x in cells) for t in range(0, 5)}
    assert costs == {0: 63, 1: 44, 2: 33, 3: 46, 4: 75}, costs
    S = [0]
    for x in cells:
        S.append(S[-1] + x)
    rows = []
    for t in range(0, 5):
        k = bisect_left(cells, t)
        rows.append((t, k, t * k - S[k], (S[9] - S[k]) - t * (9 - k)))
    assert rows == [(0, 0, 0, 21), (1, 1, 1, 13), (2, 2, 3, 6), (3, 5, 8, 2), (4, 7, 15, 0)], rows
    rng = random.Random(12984)
    for _ in range(2000):
        N = rng.randint(1, 5)
        land = [[rng.randint(0, 12) for _ in range(N)] for _ in range(N)]
        P, Q = rng.randint(1, 10), rng.randint(1, 10)
        assert solution(land, P, Q) == by_every_height(land, P, Q), (land, P, Q)
    # 300×300, 높이 10억까지
    land = [[rng.randint(0, 10 ** 9) for _ in range(300)] for _ in range(300)]
    t0 = time.perf_counter()
    solution(land, 37, 81)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"300x300: {t:.2f}s")
    print("ALL CHECKS PASSED")
