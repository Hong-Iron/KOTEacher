"""튜플 (프로그래머스 64065) 풀이와 검증."""
import random
import re
from collections import Counter


def solution(s):
    groups = s[2:-2].split("},{")
    groups = sorted((list(map(int, g.split(","))) for g in groups), key=len)
    answer, seen = [], set()
    for g in groups:
        for x in g:
            if x not in seen:
                seen.add(x)
                answer.append(x)
    return answer


def solution_count(s):
    count = Counter(re.findall(r"\d+", s))
    return [int(x) for x, _ in count.most_common()]


def encode(tup, rng):
    """튜플을 문제 규칙대로(바깥·안쪽 순서를 섞어) 문자열로 만든다."""
    groups = []
    for k in range(1, len(tup) + 1):
        g = tup[:k]
        rng.shuffle(g)
        groups.append("{" + ",".join(map(str, g)) + "}")
    rng.shuffle(groups)
    return "{" + ",".join(groups) + "}"


if __name__ == "__main__":
    ex = [("{{2},{2,1},{2,1,3},{2,1,3,4}}", [2, 1, 3, 4]), ("{{1,2,3},{2,1},{1,2,4,3},{2}}", [2, 1, 3, 4]),
          ("{{20,111},{111}}", [111, 20]), ("{{123}}", [123]), ("{{4,2,3},{3},{2,3,4,1},{2,3}}", [3, 2, 4, 1]),
          ("{{2,1},{2},{2,1,3}}", [2, 1, 3])]
    for s, want in ex:
        assert solution(s) == want == solution_count(s), s
    rng = random.Random(64065)
    for _ in range(2000):
        n = rng.randint(1, 30)
        tup = rng.sample(range(1, 100001), n)
        s = encode(tup[:], rng)
        assert solution(s) == tup == solution_count(s)
    print("ALL CHECKS PASSED")
