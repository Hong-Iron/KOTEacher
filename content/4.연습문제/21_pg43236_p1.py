"""징검다리 (프로그래머스 43236) 풀이와 검증."""
import random
import time
from itertools import combinations


def solution(distance, rocks, n):
    rocks = sorted(rocks)

    def removed_needed(d):                    # 모든 간격을 d 이상으로 만들려면 몇 개를 없애야 하나
        cnt, prev = 0, 0
        for x in rocks + [distance]:
            if x - prev < d:
                cnt += 1                      # x를 없앤다(도착점이면 직전 바위를 없앤 것으로 센다)
            else:
                prev = x
        return cnt

    lo, hi = 0, distance
    while lo < hi:                            # 최대형 틀
        mid = (lo + hi + 1) // 2
        if removed_needed(mid) <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo


def by_removing(distance, rocks, n):
    """없앨 바위 n개를 모두 골라 본다."""
    best = 0
    for gone in combinations(range(len(rocks)), n):
        s = set(gone)
        pts = [0] + sorted(r for i, r in enumerate(rocks) if i not in s) + [distance]
        best = max(best, min(b - a for a, b in zip(pts, pts[1:])))
    return best


if __name__ == "__main__":
    assert solution(25, [2, 14, 11, 21, 17], 2) == 4 == by_removing(25, [2, 14, 11, 21, 17], 2)
    # 6단계 추적: 판정 값
    rocks = sorted([2, 14, 11, 21, 17])

    def need(d):
        cnt, prev = 0, 0
        for x in rocks + [25]:
            if x - prev < d:
                cnt += 1
            else:
                prev = x
        return cnt
    assert [need(d) for d in (13, 6, 3, 4, 5)] == [5, 3, 1, 2, 3]
    lo, hi, mids = 0, 25, []
    while lo < hi:
        mid = (lo + hi + 1) // 2
        mids.append(mid)
        if need(mid) <= 2:
            lo = mid
        else:
            hi = mid - 1
    assert mids == [13, 6, 3, 4, 5] and lo == 4
    rng = random.Random(43236)
    for _ in range(3000):
        dist = rng.randint(2, 30)
        k = rng.randint(1, min(7, dist - 1))
        rs = rng.sample(range(1, dist), k)          # 서로 다른 위치
        n = rng.randint(1, k)
        assert solution(dist, rs, n) == by_removing(dist, rs, n), (dist, rs, n)
    # 바위를 모두 없애면 답은 distance
    assert solution(10, [3, 6], 2) == 10
    big = random.Random(1).sample(range(1, 1_000_000_000), 50_000)
    t0 = time.perf_counter()
    solution(1_000_000_000, big, 25_000)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"50k rocks: {t:.2f}s")
    print("ALL CHECKS PASSED")
