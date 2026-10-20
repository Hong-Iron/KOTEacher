"""가장 많이 받은 선물 (프로그래머스 258712) 풀이와 검증."""
import random
from collections import Counter


def solution(friends, gifts):
    n = len(friends)
    idx = {name: i for i, name in enumerate(friends)}
    give = [[0] * n for _ in range(n)]
    gave, got = [0] * n, [0] * n
    for g in gifts:
        a, b = g.split()
        i, j = idx[a], idx[b]
        give[i][j] += 1
        gave[i] += 1
        got[j] += 1
    point = [gave[i] - got[i] for i in range(n)]
    receive = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if give[i][j] > give[j][i]:
                receive[i] += 1
            elif give[i][j] < give[j][i]:
                receive[j] += 1
            elif point[i] > point[j]:
                receive[i] += 1
            elif point[i] < point[j]:
                receive[j] += 1
    return max(receive)


def other(friends, gifts):
    """이름 그대로 세고, 모든 순서쌍에서 '앞사람이 받는가'만 센다."""
    pair = Counter(tuple(g.split()) for g in gifts)
    gave = Counter(g.split()[0] for g in gifts)
    got = Counter(g.split()[1] for g in gifts)
    best = 0
    for a in friends:
        cnt = 0
        for b in friends:
            if a == b:
                continue
            ab, ba = pair[(a, b)], pair[(b, a)]
            pa, pb = gave[a] - got[a], gave[b] - got[b]
            if ab > ba or (ab == ba and pa > pb):
                cnt += 1
        best = max(best, cnt)
    return best


if __name__ == "__main__":
    assert solution(["muzi", "ryan", "frodo", "neo"],
                    ["muzi frodo", "muzi frodo", "ryan muzi", "ryan muzi", "ryan muzi", "frodo muzi", "frodo ryan", "neo muzi"]) == 2
    assert solution(["joy", "brad", "alessandro", "conan", "david"],
                    ["alessandro brad", "alessandro joy", "alessandro conan", "david alessandro", "alessandro david"]) == 4
    assert solution(["a", "b", "c"], ["a b", "b a", "c a", "a c", "a c", "c a"]) == 0
    assert solution(["a", "b", "c"], ["a b", "a b", "b a", "c a"]) == 2
    rng = random.Random(258712)
    for _ in range(1000):
        friends = [f"f{i}" for i in range(rng.randint(2, 7))]
        gifts = []
        for _ in range(rng.randint(1, 30)):
            a, b = rng.sample(friends, 2)
            gifts.append(f"{a} {b}")
        assert solution(friends, gifts) == other(friends, gifts)
    print("ALL CHECKS PASSED")
