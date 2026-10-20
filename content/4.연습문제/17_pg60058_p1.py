"""괄호 변환 (프로그래머스 60058) 풀이와 검증."""
from itertools import product


def is_correct(s):
    bal = 0
    for ch in s:
        bal += 1 if ch == "(" else -1
        if bal < 0:
            return False
    return bal == 0


def solution(p):
    if p == "":
        return ""
    bal = 0
    for i, ch in enumerate(p):
        bal += 1 if ch == "(" else -1
        if bal == 0:
            u, v = p[:i + 1], p[i + 1:]
            break
    if is_correct(u):
        return u + solution(v)
    flipped = "".join("(" if ch == ")" else ")" for ch in u[1:-1])
    return "(" + solution(v) + ")" + flipped


if __name__ == "__main__":
    assert solution("(()())()") == "(()())()"
    assert solution(")(") == "()"
    assert solution("()))((()") == "()(())()"
    assert solution("))((") == "()()"
    count = 0
    for n in range(2, 13, 2):
        for t in product("()", repeat=n):
            p = "".join(t)
            if p.count("(") != p.count(")"):
                continue
            count += 1
            r = solution(p)
            assert is_correct(r) and len(r) == len(p), (p, r)
            if is_correct(p):
                assert r == p
    assert count == 1274, count
    print("ALL CHECKS PASSED")
