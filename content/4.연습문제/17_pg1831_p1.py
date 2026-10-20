"""4단 고음 (프로그래머스 1831) 풀이와 검증."""
import sys
import time


def solution(n):
    def go(v, plus):                         # 끝에서부터 되돌아간다. plus: 짝을 기다리는 + 수
        if v == 1:
            return 1 if plus == 0 else 0
        if v < 1 or 3 ** (plus // 2 + plus % 2) > v:   # 남은 +를 짝지을 *가 들어갈 자리가 없다
            return 0
        cnt = go(v - 1, plus + 1)           # 마지막 글자가 +
        if v % 3 == 0 and plus >= 2:        # 마지막 글자가 * (뒤에 + 두 개가 있어야 한다)
            cnt += go(v // 3, plus - 2)
        return cnt

    return go(n, 0)


def by_forward(limit):
    """앞에서부터 올바른 문자열을 모두 만들어, 음높이가 limit 이하인 것의 개수를 음높이별로 센다."""
    cnt = {}

    def go(v, stars, pluses, s):
        if v > limit:
            return
        if stars > 0 and pluses == 2 * stars:
            cnt[v] = cnt.get(v, 0) + 1
        go(v * 3, stars + 1, pluses, s + "*")
        if pluses + 1 <= 2 * stars:
            go(v + 1, stars, pluses + 1, s + "+")

    go(1, 0, 0, "")
    return cnt


def by_grammar(max_len):
    """문제의 규칙 그대로: 3단 고음 S = * (S들) + (S들) + (S들), 올바른 문자열은 S를 하나 이상 이은 것."""
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def seq(n):                               # 길이 n인 "S를 0개 이상 이은 것"
        if n == 0:
            return frozenset([""])
        out = set()
        for k in range(3, n + 1, 3):
            for a in S(k):
                for b in seq(n - k):
                    out.add(a + b)
        return frozenset(out)

    @lru_cache(maxsize=None)
    def S(n):
        out = set()
        for i in range(0, n - 2, 3):
            for j in range(0, n - 2 - i, 3):
                k = n - 3 - i - j
                for a in seq(i):
                    for b in seq(j):
                        for c in seq(k):
                            out.add("*" + a + "+" + b + "+" + c)
        return frozenset(out)

    return {n: seq(n) for n in range(3, max_len + 1, 3)}


def is_valid(s):
    stars = pluses = 0
    for ch in s:
        if ch == "*":
            stars += 1
        else:
            pluses += 1
            if pluses > 2 * stars:
                return False
    return stars > 0 and pluses == 2 * stars


def pitch(s):
    v = 1
    for ch in s:
        v = v * 3 if ch == "*" else v + 1
    return v


if __name__ == "__main__":
    for n, want in ((15, 1), (24, 0), (41, 2)):
        assert solution(n) == want
    assert pitch("*+*+++") == 15 and pitch("**++++*++") == 41 and pitch("*+**+++++") == 41
    assert is_valid("*++*++") and is_valid("*+*+++") and not is_valid("+**+++") and not is_valid("*+++*+")
    # 6단계 추적: n = 15에서 들른 (값, 짝을 기다리는 + 수)
    calls = []

    def traced(v, plus):
        calls.append((v, plus))
        if v == 1:
            return 1 if plus == 0 else 0
        if v < 1 or 3 ** (plus // 2 + plus % 2) > v:
            return 0
        c = traced(v - 1, plus + 1)
        if v % 3 == 0 and plus >= 2:
            c += traced(v // 3, plus - 2)
        return c
    assert traced(15, 0) == 1
    assert calls == [(15, 0), (14, 1), (13, 2), (12, 3), (11, 4), (10, 5), (4, 1), (3, 2), (2, 3), (1, 0)]
    # 문법 그대로 만든 문자열 = "앞부분마다 + 수 ≤ 2 × * 수, 끝에서 같음" 조건을 만족하는 문자열 (길이 12 이하)
    from itertools import product
    g = by_grammar(12)
    for n, strs in g.items():
        ballot = {"".join(p) for p in product("*+", repeat=n) if is_valid("".join(p))}
        assert strs == ballot, n
    # 앞에서부터 모두 만든 개수와 비교(음높이 2,000 이하)
    table = by_forward(2000)
    for n in range(5, 2001):
        assert solution(n) == table.get(n, 0), n
    t0 = time.perf_counter()
    assert solution(2 ** 31 - 1) == 1735
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"n = 2^31 - 1: {t:.2f}s")
    print("ALL CHECKS PASSED")
