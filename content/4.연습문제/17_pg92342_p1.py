"""양궁대회 (프로그래머스 92342) 풀이와 검증."""
import random
from itertools import combinations_with_replacement


def solution(n, info):
    best_diff, best = 0, [-1]
    ryan = [0] * 11

    def go(i, left):
        nonlocal best_diff, best
        if i == 10:
            ryan[10] = left
            r = a = 0
            for k in range(10):
                if ryan[k] > info[k]:
                    r += 10 - k
                elif info[k] > 0:
                    a += 10 - k
            diff = r - a
            if diff > best_diff or (diff == best_diff and diff > 0 and ryan[::-1] > best[::-1]):
                best_diff, best = diff, ryan[:]
            ryan[10] = 0
            return
        need = info[i] + 1
        if need <= left:
            ryan[i] = need
            go(i + 1, left - need)
            ryan[i] = 0
        go(i + 1, left)

    go(0, n)
    return best


def score(ryan, info):
    r = a = 0
    for k in range(10):
        if ryan[k] > info[k]:
            r += 10 - k
        elif info[k] > 0:
            a += 10 - k
    return r, a


def brute(n, info):
    best_diff, best = 0, [-1]
    for combo in combinations_with_replacement(range(11), n):
        ryan = [0] * 11
        for c in combo:
            ryan[c] += 1
        r, a = score(ryan, info)
        d = r - a
        if d > best_diff or (d == best_diff and d > 0 and ryan[::-1] > best[::-1]):
            best_diff, best = d, ryan
    return best


if __name__ == "__main__":
    assert solution(5, [2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]) == [0, 2, 2, 0, 1, 0, 0, 0, 0, 0, 0]
    assert solution(1, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]) == [-1]
    assert solution(9, [0, 0, 1, 2, 0, 1, 1, 1, 1, 1, 1]) == [1, 1, 2, 0, 1, 2, 2, 0, 0, 0, 0]
    assert solution(10, [0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 3]) == [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 2]
    assert solution(2, [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]) == [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # 6단계 표
    ap = [2, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    assert score([0, 2, 2, 0, 1, 0, 0, 0, 0, 0, 0], ap) == (23, 17)
    assert score([3, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0], ap) == (19, 15)
    assert score([0, 2, 0, 0, 1, 1, 1, 0, 0, 0, 0], ap) == (24, 25)
    assert score([0] * 11, ap) == (0, 34)
    rng = random.Random(92342)
    for _ in range(1500):
        n = rng.randint(1, 6)
        info = [0] * 11
        for _ in range(n):
            info[rng.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10] if rng.random() < 0.5 else [0, 1, 2])] += 1
        assert solution(n, info) == brute(n, info), (n, info)
    print("ALL CHECKS PASSED")
