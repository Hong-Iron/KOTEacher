"""도둑질 (프로그래머스 42897) 풀이와 검증."""
import random
import time


def best_line(a):
    """한 줄로 놓인 집에서 이웃한 두 집을 털지 않는 최대 금액."""
    prev2, prev1 = 0, 0                       # dp[i-2], dp[i-1]
    for x in a:
        prev2, prev1 = prev1, max(prev1, prev2 + x)
    return prev1


def solution(money):
    # 첫 집과 마지막 집은 이웃이라 둘 중 하나는 안 턴다
    return max(best_line(money[:-1]), best_line(money[1:]))


def by_subsets(money):
    n = len(money)
    best = 0
    for mask in range(1 << n):
        ok = all(not ((mask >> i) & 1 and (mask >> ((i + 1) % n)) & 1) for i in range(n))
        if ok:
            best = max(best, sum(money[i] for i in range(n) if (mask >> i) & 1))
    return best


if __name__ == "__main__":
    assert solution([1, 2, 3, 1]) == 4 == by_subsets([1, 2, 3, 1])
    # 6단계 추적: [2, 7, 9, 3, 1] 한 줄의 dp
    dp, p2, p1 = [], 0, 0
    for x in [2, 7, 9, 3, 1]:
        p2, p1 = p1, max(p1, p2 + x)
        dp.append(p1)
    assert dp == [2, 7, 11, 11, 12]
    assert solution([2, 7, 9, 3, 1]) == 11 == by_subsets([2, 7, 9, 3, 1])
    assert (best_line([2, 7, 9, 3]), best_line([7, 9, 3, 1])) == (11, 10)
    alt = [5, 1, 1, 5, 1, 1]                                  # 짝수·홀수 번째 합은 둘 다 7
    assert sum(alt[0::2]) == sum(alt[1::2]) == 7 and solution(alt) == 10 == by_subsets(alt)
    rng = random.Random(42897)
    for _ in range(3000):
        m = [rng.randint(0, 20) for _ in range(rng.randint(3, 12))]
        assert solution(m) == by_subsets(m), m
    big = [rng.randint(0, 1000) for _ in range(1_000_000)]
    t0 = time.perf_counter()
    solution(big)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"1M houses: {t:.2f}s")
    print("ALL CHECKS PASSED")
