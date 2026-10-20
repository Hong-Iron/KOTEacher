"""순위 검색 (프로그래머스 72412) 풀이와 검증."""
import random
from bisect import bisect_left
from collections import defaultdict
from itertools import product


def solution(info, query):
    groups = defaultdict(list)
    for line in info:
        *fields, score = line.split()
        for key in product(*[(f, "-") for f in fields]):
            groups[key].append(int(score))
    for scores in groups.values():
        scores.sort()
    answer = []
    for q in query:
        parts = q.replace(" and ", " ").split()
        key, x = tuple(parts[:4]), int(parts[4])
        scores = groups.get(key, [])
        answer.append(len(scores) - bisect_left(scores, x))
    return answer


def slow(info, query):
    people = [line.split() for line in info]
    out = []
    for q in query:
        conds = q.split(" and ")
        last, x = conds[3].split()
        conds = conds[:3] + [last]
        cnt = 0
        for p in people:
            if all(c == "-" or c == v for c, v in zip(conds, p[:4])) and int(p[4]) >= int(x):
                cnt += 1
        out.append(cnt)
    return out


OPTS = [["cpp", "java", "python"], ["backend", "frontend"], ["junior", "senior"], ["chicken", "pizza"]]

if __name__ == "__main__":
    info = ["java backend junior pizza 150", "python frontend senior chicken 210", "python frontend senior chicken 150",
            "cpp backend senior pizza 260", "java backend junior chicken 80", "python backend senior chicken 50"]
    query = ["java and backend and junior and pizza 100", "python and frontend and senior and chicken 200",
             "cpp and - and senior and pizza 250", "- and backend and senior and - 150",
             "- and - and - and chicken 100", "- and - and - and - 150"]
    assert solution(info, query) == [1, 1, 1, 1, 2, 4] == slow(info, query)
    rng = random.Random(72412)
    for _ in range(1000):
        inf = [" ".join(rng.choice(o) for o in OPTS) + f" {rng.randint(1, 50)}" for _ in range(rng.randint(1, 30))]
        qs = [" and ".join(rng.choice(o + ["-"]) for o in OPTS) + f" {rng.randint(1, 50)}" for _ in range(rng.randint(1, 30))]
        assert solution(inf, qs) == slow(inf, qs)
    print("ALL CHECKS PASSED")
