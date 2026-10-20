"""신고 결과 받기 (프로그래머스 92334) 풀이와 검증."""
import random


def solution(id_list, report, k):
    reporters = {name: set() for name in id_list}
    for r in set(report):
        a, b = r.split()
        reporters[b].add(a)
    mail = {name: 0 for name in id_list}
    for b, who in reporters.items():
        if len(who) >= k:
            for a in who:
                mail[a] += 1
    return [mail[name] for name in id_list]


def brute(id_list, report, k):
    pairs = []
    for r in report:
        p = tuple(r.split())
        if p not in pairs:
            pairs.append(p)
    banned = [b for b in id_list if sum(1 for x, y in pairs if y == b) >= k]
    return [sum(1 for x, y in pairs if x == a and y in banned) for a in id_list]


if __name__ == "__main__":
    assert solution(["muzi", "frodo", "apeach", "neo"],
                    ["muzi frodo", "apeach frodo", "frodo neo", "muzi neo", "apeach muzi"], 2) == [2, 1, 1, 0]
    assert solution(["con", "ryan"], ["ryan con", "ryan con", "ryan con", "ryan con"], 3) == [0, 0]
    assert solution(["a", "b", "c"], ["a b", "a b", "c b", "b a"], 2) == [1, 0, 1]
    # dict.fromkeys(..., set())는 같은 집합을 나눠 쓴다
    shared = dict.fromkeys(["x", "y"], set())
    shared["x"].add(1)
    assert shared["y"] == {1}
    rng = random.Random(92334)
    for _ in range(1000):
        ids = [f"u{i}" for i in range(rng.randint(2, 8))]
        report = []
        for _ in range(rng.randint(1, 25)):
            a, b = rng.sample(ids, 2)
            report.append(f"{a} {b}")
        k = rng.randint(1, 4)
        assert solution(ids, report, k) == brute(ids, report, k)
    print("ALL CHECKS PASSED")
