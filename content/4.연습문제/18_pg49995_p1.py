"""쿠키 구입 (프로그래머스 49995) 풀이와 검증."""
import random
import time


def solution(cookie):
    n, best = len(cookie), 0
    for m in range(n - 1):                    # 첫째는 m에서 끝나고, 둘째는 m+1에서 시작한다
        l, r = m, m + 1
        ls, rs = cookie[l], cookie[r]
        while True:
            if ls == rs and ls > best:
                best = ls
            if ls <= rs:                       # 왼쪽이 작거나 같으면 왼쪽을 넓힌다
                if l == 0:
                    break
                l -= 1
                ls += cookie[l]
            else:                              # 오른쪽이 작으면 오른쪽을 넓힌다
                if r == n - 1:
                    break
                r += 1
                rs += cookie[r]
    return best


def trace_split(cookie, m):
    n = len(cookie)
    l, r = m, m + 1
    ls, rs = cookie[l], cookie[r]
    rows = []
    while True:
        rows.append((l, r, ls, rs))
        if ls <= rs:
            if l == 0:
                break
            l -= 1
            ls += cookie[l]
        else:
            if r == n - 1:
                break
            r += 1
            rs += cookie[r]
    return rows


def by_prefix(cookie):
    n = len(cookie)
    P = [0]
    for x in cookie:
        P.append(P[-1] + x)
    best = 0
    for l in range(n):
        for m in range(l, n - 1):
            a = P[m + 1] - P[l]
            for r in range(m + 1, n):
                if P[r + 1] - P[m + 1] == a:
                    best = max(best, a)
    return best


if __name__ == "__main__":
    assert solution([1, 1, 2, 3]) == 3 == by_prefix([1, 1, 2, 3])
    assert solution([1, 2, 4, 5]) == 0 == by_prefix([1, 2, 4, 5])
    # 6단계 추적: [1, 1, 2, 3]에서 경계가 2번째와 3번째 바구니 사이(0부터 m = 1)일 때
    assert trace_split([1, 1, 2, 3], 1) == [(1, 2, 1, 2), (0, 2, 2, 2), ]
    assert trace_split([1, 1, 2, 3], 2) == [(2, 3, 2, 3), (1, 3, 3, 3), (0, 3, 4, 3)]
    rng = random.Random(49995)
    for _ in range(3000):
        c = [rng.randint(1, 6) for _ in range(rng.randint(1, 12))]
        assert solution(c) == by_prefix(c), c
    big = [rng.randint(1, 500) for _ in range(2000)]
    t0 = time.perf_counter()
    solution(big)
    t = time.perf_counter() - t0
    same = [1] * 2000                           # 끝까지 넓혀 가는 최악
    t0 = time.perf_counter()
    assert solution(same) == 1000
    t = max(t, time.perf_counter() - t0)
    assert t < 10, t
    print(f"2000 baskets: {t:.2f}s")
    print("ALL CHECKS PASSED")
