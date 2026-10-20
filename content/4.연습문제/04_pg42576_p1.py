"""완주하지 못한 선수 (프로그래머스 42576) 풀이와 검증."""
import random
from collections import Counter


def solution(participant, completion):
    count = {}
    for name in participant:
        count[name] = count.get(name, 0) + 1
    for name in completion:
        count[name] -= 1
    for name, c in count.items():
        if c > 0:
            return name


def solution_counter(participant, completion):
    left = Counter(participant) - Counter(completion)
    return list(left)[0]


def solution_sort(participant, completion):
    p, c = sorted(participant), sorted(completion)
    for a, b in zip(p, c):
        if a != b:
            return a
    return p[-1]


if __name__ == "__main__":
    ex = [
        (["leo", "kiki", "eden"], ["eden", "kiki"], "leo"),
        (["marina", "josipa", "nikola", "vinko", "filipa"], ["josipa", "filipa", "marina", "nikola"], "vinko"),
        (["mislav", "stanko", "mislav", "ana"], ["stanko", "ana", "mislav"], "mislav"),
        (["kim", "lee", "kim"], ["lee", "kim"], "kim"),
    ]
    for p, c, want in ex:
        for f in (solution, solution_counter, solution_sort):
            assert f(p, c) == want, (f.__name__, p, c)
    # 집합의 차는 동명이인에서 틀린다
    assert set(["kim", "lee", "kim"]) - set(["lee", "kim"]) == set()
    rng = random.Random(42576)
    for _ in range(2000):
        pool = [f"n{i}" for i in range(rng.randint(1, 6))]
        participant = [rng.choice(pool) for _ in range(rng.randint(1, 30))]
        missing = rng.randrange(len(participant))
        completion = participant[:missing] + participant[missing + 1:]
        rng.shuffle(completion)
        want = participant[missing]
        for f in (solution, solution_counter, solution_sort):
            assert f(participant, completion) == want
    print("ALL CHECKS PASSED")
