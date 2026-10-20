"""문자열의 아름다움 (프로그래머스 68938) 풀이와 검증."""
import math
import random
import time
from collections import defaultdict


def solution(s):
    n = len(s)
    total = (n + 1) * n * (n - 1) // 6        # 모든 부분 문자열의 (길이 − 1) 합
    runs = defaultdict(list)                   # 글자 → 그 글자가 연달아 나온 덩어리의 길이들
    i = 0
    while i < n:
        j = i
        while j < n and s[j] == s[i]:
            j += 1
        p = j - i
        total -= (p + 1) * p * (p - 1) // 6    # 한 덩어리 안의 부분 문자열은 아름다움 0
        runs[s[i]].append(p)
        i = j
    for lens in runs.values():
        lens.sort()
        s1 = s2 = 0                            # 앞에서 본 p들의 p(p+1)(1−p)/6 합, p(p+1)/2 합
        for q in lens:
            total -= s1 + q * s2               # 짧거나 같은 덩어리 p와의 짝: f(p, q)를 모두 뺀다
            s1 += q * (q + 1) * (1 - q) // 6
            s2 += q * (q + 1) // 2
    return total


def beauty(x):
    return max((j - i for i in range(len(x)) for j in range(i + 1, len(x)) if x[i] != x[j]), default=0)


def by_definition(s):
    return sum(beauty(s[l:r + 1]) for l in range(len(s)) for r in range(l, len(s)))


def f(p, q):
    return sum(min(a, b) for a in range(1, p + 1) for b in range(1, q + 1))


if __name__ == "__main__":
    assert solution("baby") == 9 == by_definition("baby")
    assert solution("oo") == 0 == by_definition("oo")
    # 1단계·3단계의 예
    assert beauty("abbca") == 3 and beauty("aabaaa") == 3 and beauty("aaa") == 0
    assert solution("aabaa") == by_definition("aabaa") == 20 - 2 - 5 == 13
    for p in range(1, 9):
        for q in range(p, 9):
            assert f(p, q) == p * (p + 1) * (3 * q + 1 - p) // 6 == f(q, p)
    assert (f(1, 1), f(1, 2), f(2, 2), f(2, 3)) == (1, 2, 5, 8)
    # 7단계: 짝의 수와 답의 크기
    assert math.comb(150_000, 2) > 11_000_000_000
    assert 4.4e15 < math.comb(300_001, 3) < 4.6e15 and solution("ab" * 150_000) == math.comb(300_001, 3) - 2 * math.comb(150_000, 2)
    assert solution("aabaa") == by_definition("aabaa") and beauty("aabaa") == 2 and beauty("bab") == 1
    rng = random.Random(68938)
    for _ in range(3000):
        s = "".join(rng.choice("ab" if rng.random() < 0.5 else "abc") for _ in range(rng.randint(1, 14)))
        assert solution(s) == by_definition(s), s
    # 30만 글자: 글자가 모두 다른 차례, 한 글자뿐, 덩어리 길이가 1, 2, 3, …으로 다 다른 경우
    many = []
    k = 1
    while sum(len(x) for x in many) < 300_000 - 2 * k:
        many += ["a" * k, "b"]
        k += 1
    tests = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(300_000)),
             "z" * 300_000, "ab" * 150_000, "".join(many)]
    t0 = time.perf_counter()
    for s in tests:
        solution(s)
    t = time.perf_counter() - t0
    assert solution("z" * 300_000) == 0
    assert t < 5, t
    print(f"30만 글자 {len(tests)}개: {t:.2f}s")
    print("ALL CHECKS PASSED")
