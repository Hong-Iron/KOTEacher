"""무지의 먹방 라이브 (프로그래머스 42891) 풀이와 검증."""
import random
import time


def solution(food_times, k):
    if sum(food_times) <= k:
        return -1
    foods = sorted((t, i + 1) for i, t in enumerate(food_times))   # 빨리 끝나는 음식부터
    n, prev = len(foods), 0
    for idx, (t, _) in enumerate(foods):
        m = n - idx                            # 아직 남은 음식 수
        layer = (t - prev) * m                 # 이 음식이 끝날 때까지 한 바퀴씩 도는 시간
        if k < layer:
            rest = sorted(i for _, i in foods[idx:])
            return rest[k % m]
        k -= layer
        prev = t
    return -1


def trace_layers(food_times, k):
    foods = sorted((t, i + 1) for i, t in enumerate(food_times))
    n, prev, rows = len(foods), 0, []
    for idx, (t, i) in enumerate(foods):
        m = n - idx
        layer = (t - prev) * m
        rows.append((i, t, m, layer, k))
        if k < layer:
            return rows
        k -= layer
        prev = t
    return rows


def by_seconds(food_times, k):
    """1초씩 그대로 흉내 낸다."""
    left = food_times[:]
    n = len(left)
    if sum(left) <= k:
        return -1
    i = 0
    for _ in range(k):
        while left[i] == 0:
            i = (i + 1) % n
        left[i] -= 1
        i = (i + 1) % n
    while left[i] == 0:
        i = (i + 1) % n
    return i + 1


if __name__ == "__main__":
    assert solution([3, 1, 2], 5) == 1 == by_seconds([3, 1, 2], 5)
    assert trace_layers([3, 1, 2], 5) == [(2, 1, 3, 3, 5), (3, 2, 2, 2, 2), (1, 3, 1, 1, 0)]
    assert solution([4, 2, 3, 6, 7, 1, 5, 8], 16) == 3 == by_seconds([4, 2, 3, 6, 7, 1, 5, 8], 16)
    assert trace_layers([4, 2, 3, 6, 7, 1, 5, 8], 16) == [(6, 1, 8, 8, 16), (2, 2, 7, 7, 8), (3, 3, 6, 6, 1)]
    rng = random.Random(42891)
    for _ in range(3000):
        ft = [rng.randint(1, 8) for _ in range(rng.randint(1, 8))]
        k = rng.randint(1, sum(ft) + 3)
        assert solution(ft, k) == by_seconds(ft, k), (ft, k)
    # 효율성: 음식 20만 개, 시간 1억까지, k 2×10^13까지
    ft = [rng.randint(1, 100_000_000) for _ in range(200_000)]
    t0 = time.perf_counter()
    assert solution(ft, sum(ft) - 1) != -1 and solution(ft, sum(ft)) == -1
    solution(ft, sum(ft) // 2)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"200k foods: {t:.2f}s")
    print("ALL CHECKS PASSED")
