"""28.최소 신장 트리: 크루스칼·프림을 모든 신장 트리를 보는 방법과 비교한다."""
import heapq
import random
from itertools import combinations


def kruskal(n, edges, log=None):
    """n: 점 1 ~ n, edges: (a, b, w). (비용 합, 고른 간선) 돌려준다."""
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total, chosen = 0, []
    for a, b, w in sorted(edges, key=lambda e: (e[2], e[0], e[1])):
        ra, rb = find(a), find(b)
        if ra == rb:
            if log is not None:
                log.append(((a, b, w), "건너뜀"))
            continue
        parent[rb] = ra
        total += w
        chosen.append((a, b, w))
        if log is not None:
            log.append(((a, b, w), "고름"))
    return total, chosen


def prim(n, edges):
    g = [[] for _ in range(n + 1)]
    for a, b, w in edges:
        g[a].append((w, b))
        g[b].append((w, a))
    seen = [False] * (n + 1)
    heap, total, cnt = [(0, 1)], 0, 0
    while heap:
        w, v = heapq.heappop(heap)
        if seen[v]:
            continue
        seen[v] = True
        total += w
        cnt += 1
        for x in g[v]:
            if not seen[x[1]]:
                heapq.heappush(heap, x)
    return total if cnt == n else None


def brute(n, edges):
    best = None
    for comb in combinations(edges, n - 1):
        parent = list(range(n + 1))

        def find(x):
            while parent[x] != x:
                x = parent[x]
            return x
        ok = True
        for a, b, _ in comb:
            ra, rb = find(a), find(b)
            if ra == rb:
                ok = False
                break
            parent[rb] = ra
        if ok:
            s = sum(w for _, _, w in comb)
            best = s if best is None else min(best, s)
    return best


if __name__ == "__main__":
    ex = [(1, 2, 4), (1, 3, 1), (2, 3, 2), (2, 4, 5), (3, 4, 8), (3, 5, 10), (4, 5, 2)]
    log = []
    total, chosen = kruskal(5, ex, log)
    assert total == 10 == prim(5, ex) == brute(5, ex)
    assert log == [((1, 3, 1), "고름"), ((2, 3, 2), "고름"), ((4, 5, 2), "고름"), ((1, 2, 4), "건너뜀"),
                   ((2, 4, 5), "고름"), ((3, 4, 8), "건너뜀"), ((3, 5, 10), "건너뜀")]
    # C1
    c1 = [(1, 2, 3), (1, 3, 1), (1, 4, 4), (2, 3, 2), (3, 4, 5)]
    assert kruskal(4, c1)[0] == 7 == brute(4, c1)
    assert [e for e in kruskal(4, c1)[1]] == [(1, 3, 1), (2, 3, 2), (1, 4, 4)]
    # C3: 최소 신장 트리 위의 길이 최단 경로는 아니다 (A=1, B=2, C=3)
    tri = [(1, 2, 2), (2, 3, 2), (1, 3, 3)]
    assert kruskal(3, tri) == (4, [(1, 2, 2), (2, 3, 2)])
    # 무작위: 연결 그래프에서 크루스칼 = 프림 = 모든 신장 트리 중 최소
    rng = random.Random(28)
    for _ in range(1500):
        n = rng.randint(2, 6)
        es = {}
        for v in range(2, n + 1):
            es[(rng.randint(1, v - 1), v)] = rng.randint(1, 9)
        for _ in range(rng.randint(0, 6)):
            a, b = sorted(rng.sample(range(1, n + 1), 2))
            es.setdefault((a, b), rng.randint(1, 9))
        E = [(a, b, w) for (a, b), w in es.items()]
        k = kruskal(n, E)
        assert k[0] == prim(n, E) == brute(n, E) and len(k[1]) == n - 1
    print("ALL CHECKS PASSED")
