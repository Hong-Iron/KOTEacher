"""보석 쇼핑 (프로그래머스 67258) 풀이와 검증."""
import random


def solution(gems, trace=None):
    kinds = len(set(gems))
    count = {}
    left = 0
    best = [1, len(gems)]
    for right, g in enumerate(gems):
        count[g] = count.get(g, 0) + 1
        while count[gems[left]] > 1:
            count[gems[left]] -= 1
            left += 1
        if len(count) == kinds and right - left < best[1] - best[0]:
            best = [left + 1, right + 1]
        if trace is not None:
            trace.append((left + 1, right + 1, best[:]))
    return best


def slow(gems):
    kinds = set(gems)
    best = None
    for i in range(len(gems)):
        for j in range(i, len(gems)):
            if set(gems[i:j + 1]) == kinds:
                if best is None or j - i < best[1] - best[0]:
                    best = [i + 1, j + 1]
                break
    return best


if __name__ == "__main__":
    tr = []
    assert solution(["DIA", "RUBY", "RUBY", "DIA", "DIA", "EMERALD", "SAPPHIRE", "DIA"], tr) == [3, 7]
    assert tr[2] == (1, 3, [1, 8]) and tr[3] == (3, 4, [1, 8]) and tr[4] == (3, 5, [1, 8])
    assert tr[5] == (3, 6, [1, 8]) and tr[6] == (3, 7, [3, 7]) and tr[7] == (3, 8, [3, 7])
    assert solution(["AA", "AB", "AC", "AA", "AC"]) == [1, 3]
    assert solution(["XYZ", "XYZ", "XYZ"]) == [1, 1]
    assert solution(["ZZZ", "YYY", "NNNN", "YYY", "BBB"]) == [1, 5]
    assert solution(["A", "B", "A", "C", "B"]) == [2, 4]
    rng = random.Random(67258)
    for _ in range(3000):
        gems = [rng.choice("ABCD"[:rng.randint(1, 4)]) for _ in range(rng.randint(1, 15))]
        assert solution(gems) == slow(gems), gems
    print("ALL CHECKS PASSED")
