"""실패율 (프로그래머스 42889) 풀이와 검증."""
import random
from fractions import Fraction


def solution(N, stages):
    cnt = [0] * (N + 2)
    for s in stages:
        cnt[s] += 1
    remain = len(stages)
    rate = {}
    for i in range(1, N + 1):
        rate[i] = cnt[i] / remain if remain > 0 else 0
        remain -= cnt[i]
    return sorted(range(1, N + 1), key=lambda i: (-rate[i], i))


def brute(N, stages):
    """스테이지마다 직접 세고, 정확한 분수로 비교한다."""
    rate = {}
    for i in range(1, N + 1):
        stay = sum(1 for s in stages if s == i)
        reach = sum(1 for s in stages if s >= i)
        rate[i] = Fraction(stay, reach) if reach else Fraction(0)
    return sorted(range(1, N + 1), key=lambda i: (-rate[i], i))


if __name__ == "__main__":
    assert solution(5, [2, 1, 2, 6, 2, 4, 3, 3]) == [3, 4, 2, 1, 5]
    assert solution(4, [4, 4, 4, 4, 4]) == [4, 1, 2, 3]
    assert solution(3, [1, 2, 2, 4]) == [2, 1, 3]
    rng = random.Random(42889)
    for _ in range(1000):
        N = rng.randint(1, 12)
        stages = [rng.randint(1, N + 1) for _ in range(rng.randint(1, 40))]
        assert solution(N, stages) == brute(N, stages), (N, stages)
    # 같은 분수는 같은 실수가 된다
    for a in range(0, 50):
        for b in range(1, 50):
            for m in range(1, 5):
                assert a / b == (a * m) / (b * m)
    print("ALL CHECKS PASSED")
