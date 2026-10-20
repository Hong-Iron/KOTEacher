"""합승 택시 요금 (프로그래머스 72413) 풀이와 검증."""
import heapq
import random
import time

INF = float("inf")


def solution(n, s, a, b, fares):
    D = [[INF] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][i] = 0
    for c, d, f in fares:
        D[c][d] = D[d][c] = f
    for k in range(1, n + 1):
        Dk = D[k]
        for i in range(1, n + 1):
            Dik = D[i][k]
            if Dik == INF:
                continue
            Di = D[i]
            for j in range(1, n + 1):
                if Dik + Dk[j] < Di[j]:
                    Di[j] = Dik + Dk[j]
    return min(D[s][k] + D[k][a] + D[k][b] for k in range(1, n + 1))


def by_dijkstra(n, s, a, b, fares):
    """s, a, b에서 다익스트라를 한 번씩 돌려 갈라지는 지점마다 더한다."""
    g = [[] for _ in range(n + 1)]
    for c, d, f in fares:
        g[c].append((d, f))
        g[d].append((c, f))

    def dij(src):
        dist = [INF] * (n + 1)
        dist[src] = 0
        h = [(0, src)]
        while h:
            d, v = heapq.heappop(h)
            if d > dist[v]:
                continue
            for u, w in g[v]:
                if d + w < dist[u]:
                    dist[u] = d + w
                    heapq.heappush(h, (d + w, u))
        return dist

    ds, da, db = dij(s), dij(a), dij(b)
    return min(ds[k] + da[k] + db[k] for k in range(1, n + 1))


def by_path_pairs(n, s, a, b, fares):
    """s→a 경로 P와 s→b 경로 Q를 모두 짝지어, 앞부분이 같은 동안 함께 탄다고 보고 센다(작은 그래프만)."""
    g = [[] for _ in range(n + 1)]
    for c, d, f in fares:
        g[c].append((d, f))
        g[d].append((c, f))

    def paths(src, dst):
        out = []

        def go(v, path, cost, seen):
            if v == dst:
                out.append((path[:], cost))
                return
            for u, w in g[v]:
                if u not in seen:
                    seen.add(u)
                    path.append((v, u, w))
                    go(u, path, cost + w, seen)
                    path.pop()
                    seen.remove(u)

        go(src, [], 0, {src})
        return out

    best = INF
    PA, PB = paths(s, a), paths(s, b)
    for P, cp in PA:
        for Q, cq in PB:
            shared = 0
            for e1, e2 in zip(P, Q):
                if e1 != e2:
                    break
                shared += e1[2]
            best = min(best, cp + cq - shared)
    return best


if __name__ == "__main__":
    exs = [
        (6, 4, 6, 2, [[4, 1, 10], [3, 5, 24], [5, 6, 2], [3, 1, 41], [5, 1, 24], [4, 6, 50], [2, 4, 66], [2, 3, 22], [1, 6, 25]], 82),
        (7, 3, 4, 1, [[5, 7, 9], [4, 6, 4], [3, 6, 1], [3, 2, 3], [2, 1, 6]], 14),
        (6, 4, 5, 6, [[2, 6, 6], [6, 3, 7], [4, 6, 7], [6, 5, 11], [2, 5, 12], [5, 3, 20], [2, 4, 8], [4, 3, 9]], 18),
    ]
    for n, s, a, b, f, want in exs:
        assert solution(n, s, a, b, f) == want == by_dijkstra(n, s, a, b, f) == by_path_pairs(n, s, a, b, f)
    # 6단계 추적: 예시 1에서 갈라지는 지점 k마다 D[s][k] + D[k][a] + D[k][b]
    n, s, a, b, f, _ = exs[0]
    D = [[INF] * (n + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][i] = 0
    for c, d, w in f:
        D[c][d] = D[d][c] = w
    for k in range(1, n + 1):
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                D[i][j] = min(D[i][j], D[i][k] + D[k][j])
    rows = [(k, D[s][k], D[k][a], D[k][b], D[s][k] + D[k][a] + D[k][b]) for k in range(1, n + 1)]
    assert rows == [(1, 10, 25, 63, 98), (2, 66, 48, 0, 114), (3, 51, 26, 22, 99),
                    (4, 0, 35, 66, 101), (5, 34, 2, 46, 82), (6, 35, 0, 48, 83)], rows
    # 무작위 비교
    rng = random.Random(72413)
    for _ in range(800):
        n = rng.randint(3, 6)
        es = {}
        for v in range(2, n + 1):
            es[tuple(sorted((rng.randint(1, v - 1), v)))] = rng.randint(1, 20)
        for _ in range(rng.randint(0, 5)):
            c, d = sorted(rng.sample(range(1, n + 1), 2))
            es.setdefault((c, d), rng.randint(1, 20))
        fares = [[c, d, w] for (c, d), w in es.items()]
        s, a, b = rng.sample(range(1, n + 1), 3)
        assert solution(n, s, a, b, fares) == by_dijkstra(n, s, a, b, fares) == by_path_pairs(n, s, a, b, fares)
    # 시간: n = 200, 간선 최대
    n = 200
    fares = [[c, d, rng.randint(1, 100_000)] for c in range(1, n + 1) for d in range(c + 1, n + 1)]
    t0 = time.perf_counter()
    r = solution(n, 1, 2, 3, fares)
    t = time.perf_counter() - t0
    assert r == by_dijkstra(n, 1, 2, 3, fares) and t < 20, t
    print(f"n=200 full: {t:.2f}s")
    print("ALL CHECKS PASSED")
