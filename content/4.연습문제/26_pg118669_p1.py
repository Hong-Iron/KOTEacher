"""등산코스 정하기 (프로그래머스 118669) 풀이와 검증."""
import heapq
import random
import time


def solution(n, paths, gates, summits):
    graph = [[] for _ in range(n + 1)]
    for i, j, w in paths:
        graph[i].append((j, w))
        graph[j].append((i, w))
    is_summit = [False] * (n + 1)
    for s in summits:
        is_summit[s] = True
    INF = float("inf")
    inten = [INF] * (n + 1)                   # inten[v]: 출입구에서 v까지 가는 길의 가장 긴 구간, 그 최솟값
    heap = []
    for g in gates:                            # 출입구를 모두 출발점으로
        inten[g] = 0
        heap.append((0, g))
    heapq.heapify(heap)
    while heap:
        d, v = heapq.heappop(heap)
        if d > inten[v] or is_summit[v]:       # 낡았거나 산봉우리면 더 나가지 않는다
            continue
        for u, w in graph[v]:
            nd = max(d, w)                     # 합이 아니라 가장 긴 구간
            if nd < inten[u]:
                inten[u] = nd
                heapq.heappush(heap, (nd, u))
    best = min((inten[s], s) for s in summits)
    return [best[1], best[0]]


def by_paths(n, paths, gates, summits):
    """출입구마다 겹치지 않는 경로를 모두 만들어 산봉우리까지의 최소 intensity를 구한다(작은 그래프만)."""
    graph = [[] for _ in range(n + 1)]
    for i, j, w in paths:
        graph[i].append((j, w))
        graph[j].append((i, w))
    gs, ss = set(gates), set(summits)
    best = {}

    def go(v, mx, seen):
        if v in ss:
            if mx < best.get(v, float("inf")):
                best[v] = mx
            return
        for u, w in graph[v]:
            if u not in seen and u not in gs:          # 중간에 다른 출입구를 지나지 않는다
                seen.add(u)
                go(u, max(mx, w), seen)
                seen.remove(u)

    for g in gates:
        go(g, 0, {g})
    m = min((x, s) for s, x in best.items())
    return [m[1], m[0]]


def rand_case(rng, n):
    edges = {}
    for v in range(2, n + 1):                          # 연결되게 먼저 나무를 만든다
        u = rng.randint(1, v - 1)
        edges[(u, v)] = rng.randint(1, 9)
    for _ in range(rng.randint(0, n)):
        a, b = sorted(rng.sample(range(1, n + 1), 2))
        edges.setdefault((a, b), rng.randint(1, 9))
    nodes = list(range(1, n + 1))
    rng.shuffle(nodes)
    k = rng.randint(1, n - 1)
    gates = nodes[:rng.randint(1, k)]
    rest = nodes[len(gates):]
    summits = rest[:rng.randint(1, len(rest))]
    return [[a, b, w] for (a, b), w in edges.items()], gates, summits


if __name__ == "__main__":
    exs = [
        (6, [[1, 2, 3], [2, 3, 5], [2, 4, 2], [2, 5, 4], [3, 4, 4], [4, 5, 3], [4, 6, 1], [5, 6, 1]], [1, 3], [5], [5, 3]),
        (7, [[1, 4, 4], [1, 6, 1], [1, 7, 3], [2, 5, 2], [3, 7, 4], [5, 6, 6]], [1], [2, 3, 4], [3, 4]),
        (7, [[1, 2, 5], [1, 4, 1], [2, 3, 1], [2, 6, 7], [4, 5, 1], [5, 6, 1], [6, 7, 1]], [3, 7], [1, 5], [5, 1]),
        (5, [[1, 3, 10], [1, 4, 20], [2, 3, 4], [2, 4, 6], [3, 5, 20], [4, 5, 6]], [1, 2], [5], [5, 6]),
    ]
    for n, p, g, s, want in exs:
        assert solution(n, p, g, s) == want == by_paths(n, p, g, s)
    # 6단계 추적: 예시 1의 꺼내는 순서와 intensity
    n, p, g, s, _ = exs[0]
    graph = [[] for _ in range(n + 1)]
    for i, j, w in p:
        graph[i].append((j, w))
        graph[j].append((i, w))
    inten = [float("inf")] * (n + 1)
    heap = []
    for x in g:
        inten[x] = 0
        heap.append((0, x))
    heapq.heapify(heap)
    order = []
    while heap:
        d, v = heapq.heappop(heap)
        if d > inten[v]:
            continue
        order.append((d, v))
        if v in s:
            continue
        for u, w in graph[v]:
            if max(d, w) < inten[u]:
                inten[u] = max(d, w)
                heapq.heappush(heap, (inten[u], u))
    assert inten[1:] == [0, 3, 0, 3, 3, 3], inten
    assert order == [(0, 1), (0, 3), (3, 2), (3, 4), (3, 5), (3, 6)], order
    # 무작위 비교
    rng = random.Random(118669)
    for _ in range(1500):
        n = rng.randint(2, 8)
        p, g, s = rand_case(rng, n)
        assert solution(n, p, g, s) == by_paths(n, p, g, s), (n, p, g, s)
    # 시간: 지점 5만 개, 등산로 20만 개
    n = 50_000
    edges = set()
    for v in range(2, n + 1):
        edges.add((rng.randint(1, v - 1), v))
    while len(edges) < 200_000:
        a, b = sorted(rng.sample(range(1, n + 1), 2))
        edges.add((a, b))
    p = [[a, b, rng.randint(1, 10_000_000)] for a, b in edges]
    nodes = list(range(1, n + 1))
    rng.shuffle(nodes)
    t0 = time.perf_counter()
    solution(n, p, nodes[:100], nodes[100:200])
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"n=50k, m=200k: {t:.2f}s")
    print("ALL CHECKS PASSED")
