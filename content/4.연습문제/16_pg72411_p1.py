"""메뉴 리뉴얼 (프로그래머스 72411) 풀이와 검증."""
import random
from collections import Counter
from itertools import combinations


def solution(orders, course):
    orders = ["".join(sorted(o)) for o in orders]
    answer = []
    for k in course:
        count = Counter()
        for o in orders:
            count.update("".join(c) for c in combinations(o, k))
        if count:
            top = max(count.values())
            if top >= 2:
                answer += [menu for menu, cnt in count.items() if cnt == top]
    return sorted(answer)


def slow(orders, course):
    letters = sorted(set("".join(orders)))
    sets = [set(o) for o in orders]
    out = []
    for k in course:
        cnt = {}
        for combo in combinations(letters, k):
            c = sum(1 for s in sets if set(combo) <= s)
            if c >= 2:
                cnt["".join(combo)] = c
        if cnt:
            top = max(cnt.values())
            out += [m for m, v in cnt.items() if v == top]
    return sorted(out)


if __name__ == "__main__":
    assert solution(["ABCFG", "AC", "CDE", "ACDE", "BCFG", "ACDEH"], [2, 3, 4]) == ["AC", "ACDE", "BCFG", "CDE"]
    assert solution(["ABCDE", "AB", "CD", "ADE", "XYZ", "XYZ", "ACD"], [2, 3, 5]) == ["ACD", "AD", "ADE", "CD", "XYZ"]
    assert solution(["XYZ", "XWY", "WXA"], [2, 3, 4]) == ["WX", "XY"]
    assert solution(["AB", "ABC", "BC"], [2]) == ["AB", "BC"]
    rng = random.Random(72411)
    for _ in range(2000):
        orders = ["".join(rng.sample("ABCDEFG", rng.randint(2, 6))) for _ in range(rng.randint(2, 7))]
        course = sorted(rng.sample(range(2, 7), rng.randint(1, 3)))
        assert solution(orders, course) == slow(orders, course), (orders, course)
    print("ALL CHECKS PASSED")
