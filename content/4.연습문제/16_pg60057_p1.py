"""문자열 압축 (프로그래머스 60057) 풀이와 검증."""
import random


def solution(s):
    best = len(s)
    for k in range(1, len(s) // 2 + 1):
        chunks = [s[i:i + k] for i in range(0, len(s), k)]
        length, count = 0, 1
        for a, b in zip(chunks, chunks[1:] + [None]):
            if a == b:
                count += 1
            else:
                length += len(a) + (len(str(count)) if count > 1 else 0)
                count = 1
        best = min(best, length)
    return best


def compress(s, k):
    out, i = [], 0
    while i < len(s):
        piece = s[i:i + k]
        cnt = 1
        while s[i + cnt * k:i + (cnt + 1) * k] == piece:
            cnt += 1
        out.append((str(cnt) if cnt > 1 else "") + piece)
        i += cnt * k
    return "".join(out)


def slow(s):
    return min(len(compress(s, k)) for k in range(1, len(s) + 1))


if __name__ == "__main__":
    ex = [("aabbaccc", 7), ("ababcdcdababcdcd", 9), ("abcabcdede", 8),
          ("abcabcabcabcdededededede", 14), ("xababcdcdababcdcd", 17), ("abab", 3)]
    for s, want in ex:
        assert solution(s) == want == slow(s), s
    assert compress("ababcdcdababcdcd", 2) == "2ab2cd2ab2cd" and compress("ababcdcdababcdcd", 8) == "2ababcdcd"
    assert solution("a" * 12) == 3 and compress("a" * 12, 1) == "12a"
    assert solution("a") == 1
    rng = random.Random(60057)
    for _ in range(3000):
        base = "".join(rng.choice("ab") for _ in range(rng.randint(1, 3)))
        s = "".join(base * rng.randint(1, 12) + rng.choice(["", "a", "b", "ab"]) for _ in range(rng.randint(1, 3)))
        assert solution(s) == slow(s), s
    print("ALL CHECKS PASSED")
