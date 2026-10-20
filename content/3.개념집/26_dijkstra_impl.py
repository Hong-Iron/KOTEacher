"""26.다익스트라: heapq로 짠 다익스트라와 문서 주장의 확인."""
import heapq
import random
import time

INF = float("inf")


def dijkstra(graph, s):
    """graph[v]: (이웃, 비용) 목록, 비용은 0 이상. dist[v]: s에서 v까지 최소 비용."""
    dist = [INF] * len(graph)
    dist[s] = 0
    heap = [(0, s)]
    while heap:
        d, v = heapq.heappop(heap)
        if d > dist[v]:                    # 낡은 기록이면 버린다
            continue
        for u, w in graph[v]:
            nd = d + w
            if nd < dist[u]:
                dist[u] = nd
                heapq.heappush(heap, (nd, u))
    return dist


def dijkstra_trace(graph, s):
    dist = [INF] * len(graph)
    dist[s] = 0
    heap, rows = [(0, s)], []
    while heap:
        d, v = heapq.heappop(heap)
        if d > dist[v]:
            rows.append(((d, v), "낡음", [], sorted(heap)))
            continue
        changed = []
        for u, w in graph[v]:
            nd = d + w
            if nd < dist[u]:
                dist[u] = nd
                heapq.heappush(heap, (nd, u))
                changed.append((u, nd))
        rows.append(((d, v), "확정", changed, sorted(heap)))
    return dist, rows


def dijkstra_no_skip(graph, s):
    """낡은 기록을 버리지 않는 방식. (거리, 이웃 목록을 훑은 횟수)를 돌려준다."""
    dist = [INF] * len(graph)
    dist[s] = 0
    heap, scans = [(0, s)], 0
    while heap:
        d, v = heapq.heappop(heap)
        scans += 1
        for u, w in graph[v]:
            if d + w < dist[u]:
                dist[u] = d + w
                heapq.heappush(heap, (dist[u], u))
    return dist, scans


def dijkstra_done_set(graph, s):
    """한 번 꺼낸 점은 다시 처리하지 않는 방식(음수 간선 반례용)."""
    dist = [INF] * len(graph)
    dist[s] = 0
    done = [False] * len(graph)
    heap = [(0, s)]
    while heap:
        d, v = heapq.heappop(heap)
        if done[v]:
            continue
        done[v] = True
        for u, w in graph[v]:
            if d + w < dist[u]:
                dist[u] = d + w
                heapq.heappush(heap, (dist[u], u))
    return dist


def mark_at_push(graph, s):
    """BFS처럼 처음 발견할 때 확정하는 잘못된 방식."""
    dist = [INF] * len(graph)
    dist[s] = 0
    seen = [False] * len(graph)
    seen[s] = True
    heap = [(0, s)]
    while heap:
        d, v = heapq.heappop(heap)
        for u, w in graph[v]:
            if not seen[u]:
                seen[u] = True
                dist[u] = d + w
                heapq.heappush(heap, (dist[u], u))
    return dist


def bellman_ford(n, edges, s):
    d = [INF] * n
    d[s] = 0
    for _ in range(n - 1):
        for a, b, w in edges:
            if d[a] + w < d[b]:
                d[b] = d[a] + w
    return d


def build(n, edges, directed=True):
    g = [[] for _ in range(n)]
    for a, b, w in edges:
        g[a].append((b, w))
        if not directed:
            g[b].append((a, w))
    return g


if __name__ == "__main__":
    # 예시로 보기: 방향 그래프 1 ~ 5 (0번은 비움)
    ex = [(1, 2, 4), (1, 3, 1), (3, 2, 2), (2, 4, 1), (3, 4, 5), (4, 5, 3)]
    g = build(6, ex)
    dist, rows = dijkstra_trace(g, 1)
    assert dist[1:] == [0, 3, 1, 4, 7]
    assert rows == [
        ((0, 1), "확정", [(2, 4), (3, 1)], [(1, 3), (4, 2)]),
        ((1, 3), "확정", [(2, 3), (4, 6)], [(3, 2), (4, 2), (6, 4)]),
        ((3, 2), "확정", [(4, 4)], [(4, 2), (4, 4), (6, 4)]),
        ((4, 2), "낡음", [], [(4, 4), (6, 4)]),
        ((4, 4), "확정", [(5, 7)], [(6, 4), (7, 5)]),
        ((6, 4), "낡음", [], [(7, 5)]),
        ((7, 5), "확정", [], []),
    ], rows
    # 낡은 기록을 버리지 않아도 거리는 같고, 훑는 횟수만 는다(예시: 7번 대 5번)
    assert dijkstra_no_skip(g, 1) == (dist, 7)
    # C1: 무방향 그래프
    c1 = [(1, 2, 7), (1, 3, 9), (1, 6, 14), (2, 3, 10), (2, 4, 15), (3, 4, 11), (3, 6, 2), (4, 5, 6), (5, 6, 9)]
    d1, r1 = dijkstra_trace(build(7, c1, directed=False), 1)
    assert d1[1:] == [0, 7, 9, 20, 20, 11]
    assert [v for (dd, v), kind, _, _ in r1 if kind == "확정"] == [1, 2, 3, 6, 4, 5]
    # 오해: 처음 발견할 때 확정하면 틀린다 (s=0, a=1, b=2)
    gm = build(3, [(0, 1, 5), (0, 2, 1), (2, 1, 1)])
    assert dijkstra(gm, 0)[1] == 2 and mark_at_push(gm, 0)[1] == 5
    # C3: 음수 간선 (s=0, a=1, b=2, c=3)
    neg = [(0, 1, 2), (0, 2, 3), (2, 1, -2), (1, 3, 1)]
    gn = build(4, neg)
    assert bellman_ford(4, neg, 0)[3] == 2 and dijkstra_done_set(gn, 0)[3] == 3
    # 무작위: 비용이 0 이상이면 벨만-포드와 같다, 힙에 넣는 횟수는 간선 수 + 1 이하
    rng = random.Random(26)
    for _ in range(2000):
        n = rng.randint(1, 9)
        es = []
        for _ in range(rng.randint(0, 16)):
            a, b = rng.randrange(n), rng.randrange(n)
            if a != b:
                es.append((a, b, rng.randint(0, 9)))
        directed = rng.random() < 0.5
        full = es if directed else es + [(b, a, w) for a, b, w in es]
        s = rng.randrange(n)
        g = build(n, full)
        pushes = [0]
        orig = heapq.heappush

        def counting(h, x):
            pushes[0] += 1
            orig(h, x)
        heapq.heappush = counting
        got = dijkstra(g, s)
        heapq.heappush = orig
        assert got == bellman_ford(n, full, s) == dijkstra_done_set(g, s) == dijkstra_no_skip(g, s)[0]
        assert pushes[0] <= len(full)
    # 시간: 점 5만 개, 간선 20만 개(무방향)
    n = 50_000
    es = [(rng.randrange(n), rng.randrange(n), rng.randint(1, 10_000_000)) for _ in range(200_000)]
    g = build(n, es, directed=False)
    t0 = time.perf_counter()
    dijkstra(g, 0)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"n=50k, m=200k: {t:.2f}s")
    print("ALL CHECKS PASSED")
