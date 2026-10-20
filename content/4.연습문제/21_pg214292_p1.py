"""재밌는 레이싱 경기장 설계하기 (프로그래머스 214292) 풀이와 검증. 인덱스는 0부터 센다."""
import random
import time
from itertools import permutations


def solution(heights):
    a = sorted(heights)
    n = len(a)
    m = n // 2
    if n % 2 == 0:
        return min(a[i + m] - a[i] for i in range(m))          # 연달아 놓인 m + 1개의 폭 중 최소
    widths = sorted(a[i + m] - a[i] for i in range(m + 1))     # 연달아 놓인 m + 1개의 폭
    return widths[1]                                           # 하나는 좁아도 된다: 두 번째로 작은 값


def arrange(heights):
    """답을 만드는 실제 배치."""
    a = sorted(heights)
    n = len(a)
    m = n // 2
    if n % 2 == 0:
        out = []
        for j in range(m):
            out += [a[m + j], a[j]]                            # 위 절반, 아래 절반을 번갈아
        return out
    t = min(range(m + 1), key=lambda i: a[i + m] - a[i])       # 가장 좁은 창의 시작
    w = [a[t + m - p] for p in range(m + 1)]                   # 창 안의 값: 홀수 번째 자리, 큰 것부터
    e = [a[t - 1 - p] for p in range(t)] + [a[t + 2 * m - p] for p in range(t, m)]   # 창 아래, 창 위
    out = []
    for p in range(m + 1):
        out.append(w[p])
        if p < m:
            out.append(e[p])
    return out


def gap(seq):
    return min(abs(seq[i] - seq[i + 1]) for i in range(len(seq) - 1))


def feasible(a, d):
    """흔한 실수 확인용: 최소 차이 d가 되는지 비트마스크로 직접 따진다(작은 입력만)."""
    n = len(a)
    ok = [[abs(a[i] - a[j]) >= d for j in range(n)] for i in range(n)]
    reach = [[False] * n for _ in range(1 << n)]
    for i in range(n):
        reach[1 << i][i] = True
    for mask in range(1 << n):
        for i in range(n):
            if reach[mask][i]:
                for j in range(n):
                    if not mask >> j & 1 and ok[i][j]:
                        reach[mask | 1 << j][j] = True
    return any(reach[(1 << n) - 1])


def by_bitmask(heights):
    a = sorted(heights)
    cands = sorted({abs(x - y) for x in a for y in a})
    lo, hi = 0, len(cands) - 1                                 # cands[0] = 0은 늘 된다
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(a, cands[mid]):
            lo = mid
        else:
            hi = mid - 1
    return cands[lo]


def zigzag_only(heights):
    """흔한 실수: 아래 절반과 위 절반을 번갈아 놓는 방법만 본다."""
    a = sorted(heights)
    n = len(a)
    m = n // 2
    if n % 2 == 0:
        return min(a[i + m] - a[i] for i in range(m))
    return max(min(a[i + m] - a[i] for i in range(m)), min(a[i + m] - a[i] for i in range(1, m + 1)))


if __name__ == "__main__":
    exs = [([1, 8, 5], 4), ([11, 6, 4, 11], 5), ([9, 9, 9, 9, 30], 0)]
    for h, want in exs:
        assert solution(h) == want == gap(arrange(h)) == by_bitmask(h), h
    # 1단계와 7단계의 예
    assert sorted(arrange([1, 3, 3, 3, 6])) == [1, 3, 3, 3, 6]
    assert arrange([1, 3, 3, 3, 6]) == [3, 1, 3, 6, 3] and solution([1, 3, 3, 3, 6]) == 2
    assert zigzag_only([1, 3, 3, 3, 6]) == 0
    assert min(b - a for a, b in zip([1, 5, 8], [5, 8])) == 3 and solution([1, 5, 8]) == 4   # 홀수에 짝수 공식을 쓰면 3
    assert arrange([11, 6, 4, 11]) == [11, 4, 11, 6]
    assert __import__("math").factorial(12) == 479_001_600
    assert solution([0, 10, 20, 30]) == 20 and arrange([0, 10, 20, 30]) == [20, 0, 30, 10]
    rng = random.Random(214292)
    for _ in range(3000):
        n = rng.randint(2, 7)
        h = [rng.randint(1, rng.choice([3, 10, 30])) for _ in range(n)]
        want = max(gap(p) for p in permutations(h))
        assert solution(h) == want == gap(arrange(h)), h
        assert sorted(arrange(h)) == sorted(h)
    for _ in range(300):
        n = rng.randint(8, 11)
        h = [rng.randint(1, rng.choice([5, 20, 100])) for _ in range(n)]
        assert solution(h) == by_bitmask(h) == gap(arrange(h)), h
    zig_wrong = sum(zigzag_only(h) != solution(h) for h in
                    ([rng.randint(1, 10) for _ in range(rng.choice([5, 7, 9]))] for _ in range(2000)))
    assert zig_wrong > 0
    # 20만 개
    h = [rng.randint(1, 10 ** 9) for _ in range(200_000)]
    t0 = time.perf_counter()
    ans = solution(h)
    t = time.perf_counter() - t0
    assert gap(arrange(h)) == ans
    h2 = h[:-1]
    assert gap(arrange(h2)) == solution(h2)
    assert t < 5, t
    print(f"n=200,000: {t:.2f}s")
    print("ALL CHECKS PASSED")
