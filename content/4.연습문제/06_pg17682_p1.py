"""다트 게임 (프로그래머스 17682) 풀이와 검증."""
import random
import re


def solution(dartResult):
    power = {"S": 1, "D": 2, "T": 3}
    scores = []
    for num, bonus, opt in re.findall(r"(\d+)([SDT])([*#]?)", dartResult):
        s = int(num) ** power[bonus]
        if opt == "*":
            s *= 2
            if scores:
                scores[-1] *= 2
        elif opt == "#":
            s = -s
        scores.append(s)
    return sum(scores)


def other(s):
    """한 글자씩 읽어 조각을 만들고, 조각마다 배수를 따로 모아 마지막에 곱한다."""
    parts, i = [], 0
    while i < len(s):
        j = i
        while s[j].isdigit():
            j += 1
        num, bonus = int(s[i:j]), s[j]
        j += 1
        opt = s[j] if j < len(s) and s[j] in "*#" else ""
        j += len(opt)
        parts.append((num, bonus, opt))
        i = j
    mult = [1] * len(parts)
    for k, (_, _, opt) in enumerate(parts):
        if opt == "*":
            mult[k] *= 2
            if k > 0:
                mult[k - 1] *= 2
        elif opt == "#":
            mult[k] *= -1
    return sum(num ** "_SDT".index(b) * m for (num, b, _), m in zip(parts, mult))


if __name__ == "__main__":
    ex = [("1S2D*3T", 37), ("1D2S#10S", 9), ("1D2S0T", 3), ("1S*2T*3S", 23),
          ("1D#2S*3S", 5), ("1T2D3D#", -4), ("1D2S3T*", 59)]
    for s, want in ex:
        assert solution(s) == want == other(s), s
    rng = random.Random(17682)
    for _ in range(3000):
        s = "".join(f"{rng.randint(0, 10)}{rng.choice('SDT')}{rng.choice(['', '*', '#'])}" for _ in range(3))
        assert solution(s) == other(s), s
    print("ALL CHECKS PASSED")
