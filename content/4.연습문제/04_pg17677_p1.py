"""뉴스 클러스터링 (프로그래머스 17677) 풀이와 검증."""
import random
from collections import Counter
from fractions import Fraction


def solution(str1, str2):
    def pairs(s):
        s = s.lower()
        return Counter(s[i:i + 2] for i in range(len(s) - 1) if s[i:i + 2].isalpha())
    a, b = pairs(str1), pairs(str2)
    inter = sum((a & b).values())
    union = sum((a | b).values())
    if union == 0:
        return 65536
    return inter * 65536 // union


def slow(str1, str2):
    def pairs(s):
        out = []
        for i in range(len(s) - 1):
            x, y = s[i].lower(), s[i + 1].lower()
            if "a" <= x <= "z" and "a" <= y <= "z":
                out.append(x + y)
        return out
    A, B = pairs(str1), pairs(str2)
    kinds = set(A) | set(B)
    inter = sum(min(A.count(k), B.count(k)) for k in kinds)
    union = sum(max(A.count(k), B.count(k)) for k in kinds)
    if union == 0:
        return 65536
    return int(Fraction(inter, union) * 65536)


if __name__ == "__main__":
    ex = [("FRANCE", "french", 16384), ("handshake", "shake hands", 65536),
          ("aa1+aa2", "AAAA12", 43690), ("E=M*C^2", "e=m*c^2", 65536), ("aab", "abb", 21845)]
    for s1, s2, want in ex:
        assert solution(s1, s2) == want == slow(s1, s2), (s1, s2)
    assert Counter(["x", "x"]) & Counter(["x"]) == Counter(["x"]) and Counter(["x", "x"]) | Counter(["x"]) == Counter(["x", "x"])
    rng = random.Random(17677)
    alpha = "aAbB c1+"
    for _ in range(3000):
        s1 = "".join(rng.choice(alpha) for _ in range(rng.randint(2, 15)))
        s2 = "".join(rng.choice(alpha) for _ in range(rng.randint(2, 15)))
        assert solution(s1, s2) == slow(s1, s2), (s1, s2)
    print("ALL CHECKS PASSED")
