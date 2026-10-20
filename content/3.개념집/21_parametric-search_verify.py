"""21.매개변수 탐색: 두 가지 틀과 문서·예제 사다리의 예시를 확인한다."""
import math
import random


def min_true(lo, hi, ok, log=None):
    """ok가 F…F T…T이고 ok(hi)가 참일 때, 참인 가장 작은 x."""
    while lo < hi:
        mid = (lo + hi) // 2
        r = ok(mid)
        if log is not None:
            log.append((lo, hi, mid, r))
        if r:
            hi = mid
        else:
            lo = mid + 1
    return lo


def max_true(lo, hi, ok, log=None):
    """ok가 T…T F…F이고 ok(lo)가 참일 때, 참인 가장 큰 x."""
    while lo < hi:
        mid = (lo + hi + 1) // 2
        r = ok(mid)
        if log is not None:
            log.append((lo, hi, mid, r))
        if r:
            lo = mid
        else:
            hi = mid - 1
    return lo


# 통나무 자르기 (문서 예시): 길이 L 토막을 k개 이상 얻는 가장 긴 L
def pieces(logs, L):
    return sum(x // L for x in logs)


# 사다리 1: 책을 순서대로 k명에게 나눌 때 가장 많이 받는 쪽수의 최솟값
def people_needed(books, cap):
    cnt, cur = 1, 0
    for b in books:
        if cur + b > cap:
            cnt, cur = cnt + 1, 0
        cur += b
    return cnt


# 사다리 2: 공유기 c개를 서로 x 이상 떨어뜨려 놓을 수 있나
def can_place(houses, c, x):
    placed, last = 1, houses[0]
    for h in houses[1:]:
        if h - last >= x:
            placed, last = placed + 1, h
    return placed >= c


# 사다리 3: 한 시간에 x개씩 먹을 때 걸리는 시간
def hours(piles, x):
    return sum((p + x - 1) // x for p in piles)


# 사다리 4: 기계들이 T초 안에 만드는 물건 수
def made(times, T):
    return sum(T // t for t in times)


def split_brute(books, k):
    best = None
    n = len(books)

    def go(i, parts, cur_max):
        nonlocal best
        if i == n:
            if parts <= k and (best is None or cur_max < best):
                best = cur_max
            return
        s = 0
        for j in range(i, n):
            s += books[j]
            go(j + 1, parts + 1, max(cur_max, s))

    go(0, 0, 0)
    return best


def place_brute(houses, c):
    from itertools import combinations
    return max(min(b - a for a, b in zip(comb, comb[1:])) for comb in combinations(sorted(houses), c))


if __name__ == "__main__":
    # 문서 예시: 통나무 [8, 5, 11], k = 5
    logs, k = [8, 5, 11], 5
    assert [pieces(logs, L) for L in range(1, 7)] == [24, 11, 6, 5, 4, 2]
    trace = []
    assert max_true(1, 11, lambda L: pieces(logs, L) >= k, trace) == 4
    assert trace == [(1, 11, 6, False), (1, 5, 3, True), (3, 5, 4, True), (4, 5, 5, False)]
    t6 = []                                            # C1: k = 6
    assert max_true(1, 11, lambda L: pieces(logs, L) >= 6, t6) == 3
    assert t6 == [(1, 11, 6, False), (1, 5, 3, True), (3, 5, 4, False)]
    # 사다리 1: 책 [10, 20, 30, 40], 2명
    books = [10, 20, 30, 40]
    t1 = []
    assert min_true(max(books), sum(books), lambda x: people_needed(books, x) <= 2, t1) == 60
    assert [m for _, _, m, _ in t1] == [70, 55, 63, 59, 61, 60]
    assert split_brute(books, 2) == 60
    # 사다리 2: 집 [1, 2, 8, 4, 9], 공유기 3개
    hs = sorted([1, 2, 8, 4, 9])
    assert max_true(1, hs[-1] - hs[0], lambda x: can_place(hs, 3, x)) == 3 == place_brute(hs, 3)
    assert can_place(hs, 3, 3) and not can_place(hs, 3, 4)
    # 개념 문서 C4: 책 [7, 2, 5, 10, 8], 2명
    b4 = [7, 2, 5, 10, 8]
    assert min_true(max(b4), sum(b4), lambda x: people_needed(b4, x) <= 2) == 18 == split_brute(b4, 2)
    assert (max(b4), sum(b4), people_needed(b4, 17)) == (10, 32, 3)
    # 사다리 3: 바나나 [3, 6, 7, 11], 8시간
    assert hours([3, 6, 7, 11], 4) == 8 and hours([3, 6, 7, 11], 3) == 10
    assert min_true(1, 11, lambda x: hours([3, 6, 7, 11], x) <= 8) == 4
    # 사다리 4: 기계 [2, 3, 7], 물건 8개
    assert made([2, 3, 7], 8) == 7 and made([2, 3, 7], 9) == 8
    assert min_true(1, 2 * 8, lambda T: made([2, 3, 7], T) >= 8) == 9
    # 무작위: 두 틀이 처음부터 세는 방법과 같다. 판정 횟수는 ⌈log2(범위 크기)⌉ 이하
    rng = random.Random(21)
    for _ in range(3000):
        lo = rng.randint(-20, 20)
        hi = lo + rng.randint(0, 60)
        th = rng.randint(lo, hi)                      # 경계
        calls = []
        f = lambda x: calls.append(x) or x >= th
        assert min_true(lo, hi, f) == th and len(calls) <= math.ceil(math.log2(hi - lo + 1))
        calls.clear()
        g = lambda x: calls.append(x) or x <= th
        assert max_true(lo, hi, g) == th and len(calls) <= math.ceil(math.log2(hi - lo + 1))
    for _ in range(300):
        books = [rng.randint(1, 20) for _ in range(rng.randint(1, 7))]
        kk = rng.randint(1, len(books))
        assert min_true(max(books), sum(books), lambda x: people_needed(books, x) <= kk) == split_brute(books, kk)
        hs = sorted(rng.sample(range(1, 30), rng.randint(2, 7)))
        c = rng.randint(2, len(hs))
        assert max_true(1, hs[-1] - hs[0], lambda x: can_place(hs, c, x)) == place_brute(hs, c)
    # 범위 1 ~ 10억에서 판정은 30번
    calls = []
    min_true(1, 10**9, lambda x: calls.append(x) or x >= 123456789)
    assert len(calls) == 30 == math.ceil(math.log2(10**9))
    # 단조가 아니면 틀린다: ok = [F, T, F, F, T] (x = 0..4) 에서 참인 가장 작은 x는 1
    vals = [False, True, False, False, True]
    assert min_true(0, 4, lambda x: vals[x]) == 4
    # 최대형에서 mid를 내림으로 잡으면 lo = hi - 1에서 멈추지 않는다
    lo, hi, spins = 3, 4, 0
    while lo < hi and spins < 100:
        mid = (lo + hi) // 2
        if mid <= 3:
            lo = mid
        else:
            hi = mid - 1
        spins += 1
    assert spins == 100 and (lo, hi) == (3, 4)
    print("ALL CHECKS PASSED")
