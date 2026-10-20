"""외벽 점검 (프로그래머스 60062) 풀이와 검증."""
import random
import time
from itertools import permutations


def solution(n, weak, dist):
    W = len(weak)
    line = weak + [w + n for w in weak]          # 원을 한 번 펼친다
    dist = sorted(dist, reverse=True)
    for k in range(1, len(dist) + 1):
        for friends in permutations(dist[:k]):   # 가장 멀리 가는 k명의 순서
            for s in range(W):                   # line[s] ~ line[s + W - 1]을 덮는다
                end = s + W
                i, used = s, 0
                while i < end and used < k:
                    reach = line[i] + friends[used]
                    used += 1
                    while i < end and line[i] <= reach:
                        i += 1
                if i == end:
                    return k
    return -1


def cover_parts(n, weak, friends, s):
    """친구 순서와 시작 번호 s가 정해졌을 때 친구마다 덮은 지점(펼친 좌표)과 성공 여부."""
    W = len(weak)
    line = weak + [w + n for w in weak]
    end, i, used, parts = s + W, s, 0, []
    while i < end and used < len(friends):
        reach, got = line[i] + friends[used], []
        used += 1
        while i < end and line[i] <= reach:
            got.append(line[i])
            i += 1
        parts.append(got)
    return parts, i == end


def trace_first_success(n, weak, dist):
    """처음 성공하는 (k, 친구 순서, 시작 번호, 각 친구가 덮은 지점들)을 돌려준다."""
    dist = sorted(dist, reverse=True)
    for k in range(1, len(dist) + 1):
        for friends in permutations(dist[:k]):
            for s in range(len(weak)):
                parts, ok = cover_parts(n, weak, friends, s)
                if ok:
                    return k, friends, s, parts
    return None


def by_cover(n, weak, dist):
    """친구마다 '안 씀' 또는 '어느 취약 지점에서 시계 방향 출발'을 모두 골라 보는 풀이."""
    arcs = {}
    for d in set(dist):
        for w in weak:
            arcs[(d, w)] = frozenset(p for p in weak if (p - w) % n <= d)
    full = frozenset(weak)
    best = [None]

    def go(i, covered, used):
        if covered == full:
            if best[0] is None or used < best[0]:
                best[0] = used
            return
        if i == len(dist):
            return
        go(i + 1, covered, used)
        for w in weak:
            go(i + 1, covered | arcs[(dist[i], w)], used + 1)

    go(0, frozenset(), 0)
    return -1 if best[0] is None else best[0]


if __name__ == "__main__":
    assert solution(12, [1, 5, 6, 10], [1, 2, 3, 4]) == 2
    assert solution(12, [1, 3, 4, 9, 10], [3, 5, 7]) == 1
    # 6단계 추적: 예시 1은 친구 (4, 3), 두 번째 지점(5)에서 시작할 때 처음 성공한다
    assert trace_first_success(12, [1, 5, 6, 10], [1, 2, 3, 4]) == (2, (4, 3), 1, [[5, 6], [10, 13]])
    assert trace_first_success(12, [1, 3, 4, 9, 10], [3, 5, 7]) == (1, (7,), 3, [[9, 10, 13, 15, 16]])
    rows = [((4,), 0, [[1, 5]]), ((4,), 1, [[5, 6]]), ((4,), 2, [[6, 10]]), ((4,), 3, [[10, 13]]),
            ((4, 3), 0, [[1, 5], [6]]), ((4, 3), 1, [[5, 6], [10, 13]])]
    for friends, st, want in rows:
        assert cover_parts(12, [1, 5, 6, 10], friends, st)[0] == want
    # 가장 먼 k명만 써도 되는지: 모든 k명 조합을 쓰는 풀이와 비교
    rng = random.Random(60062)
    for _ in range(600):
        n = rng.randint(3, 20)
        weak = sorted(rng.sample(range(n), rng.randint(1, min(n, 6))))
        dist = [rng.randint(1, 8) for _ in range(rng.randint(1, 4))]
        assert solution(n, weak, dist) == by_cover(n, weak, dist), (n, weak, dist)
    # 최악: 취약 지점 15개, 친구 8명이 모두 필요하거나 모두 보내도 안 될 때
    worst = 0.0
    for dist in ([1] * 8, [12] * 7 + [1], [25] * 6 + [1, 1]):
        weak = list(range(0, 200, 13))[:15]
        t0 = time.perf_counter()
        solution(200, weak, dist)
        worst = max(worst, time.perf_counter() - t0)
    assert solution(200, list(range(0, 200, 13))[:15], [1] * 8) == -1
    assert worst < 5, worst
    print(f"worst {worst:.2f}s")
    print("ALL CHECKS PASSED")
