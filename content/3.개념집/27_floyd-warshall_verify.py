"""27.플로이드–워셜: 예시 표, 반복 순서, 음수 사이클 판정을 확인한다."""
import random
import time

INF = float("inf")


def matrix(n, edges, directed=False):
    D = [[INF] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        D[i][i] = 0
    for a, b, w in edges:
        D[a][b] = min(D[a][b], w)
        if not directed:
            D[b][a] = min(D[b][a], w)
    return D


def floyd(D, n, snapshots=None):
    for k in range(1, n + 1):             # 거쳐 가도 되는 점을 하나씩 늘린다
        for i in range(1, n + 1):
            for j in range(1, n + 1):
                if D[i][k] + D[k][j] < D[i][j]:
                    D[i][j] = D[i][k] + D[k][j]
        if snapshots is not None:
            snapshots.append([row[1:] for row in D[1:]])
    return D


def floyd_wrong(D, n):
    for i in range(1, n + 1):             # k를 가장 안쪽에 둔 잘못된 순서
        for j in range(1, n + 1):
            for k in range(1, n + 1):
                if D[i][k] + D[k][j] < D[i][j]:
                    D[i][j] = D[i][k] + D[k][j]
    return D


def bellman_ford(n, edges, s):
    d = [INF] * (n + 1)
    d[s] = 0
    for _ in range(n - 1):
        for a, b, w in edges:
            if d[a] + w < d[b]:
                d[b] = d[a] + w
    neg = any(d[a] + w < d[b] for a, b, w in edges if d[a] < INF)
    return d, neg


if __name__ == "__main__":
    # 예시로 보기: 무방향 1–2(5), 1–4(9), 2–3(2), 3–4(1)
    D = matrix(4, [(1, 2, 5), (1, 4, 9), (2, 3, 2), (3, 4, 1)])
    assert [row[1:] for row in D[1:]] == [[0, 5, INF, 9], [5, 0, 2, INF], [INF, 2, 0, 1], [9, INF, 1, 0]]
    snaps = []
    floyd(D, 4, snaps)
    assert snaps[0] == [[0, 5, INF, 9], [5, 0, 2, 14], [INF, 2, 0, 1], [9, 14, 1, 0]]
    assert snaps[1] == [[0, 5, 7, 9], [5, 0, 2, 14], [7, 2, 0, 1], [9, 14, 1, 0]]
    assert snaps[2] == [[0, 5, 7, 8], [5, 0, 2, 3], [7, 2, 0, 1], [8, 3, 1, 0]]
    assert snaps[3] == snaps[2]
    # C1: 방향 1→2(1), 2→3(1), 1→3(5), 3→1(1)
    C = floyd(matrix(3, [(1, 2, 1), (2, 3, 1), (1, 3, 5), (3, 1, 1)], directed=True), 3)
    assert [row[1:] for row in C[1:]] == [[0, 1, 2], [2, 0, 1], [1, 2, 0]]
    # C3: k를 안쪽에 두면 1→2→4→3을 놓친다
    es = [(1, 2, 4), (2, 4, 1), (4, 3, 5)]
    assert floyd(matrix(4, es, True), 4)[1][3] == 10 and floyd_wrong(matrix(4, es, True), 4)[1][3] == INF
    # 무작위: 음수 간선 포함, 음수 사이클이 없으면 벨만-포드와 같고, 있으면 어떤 D[i][i] < 0
    rng = random.Random(27)
    neg_seen = 0
    for _ in range(1500):
        n = rng.randint(1, 6)
        es = []
        for _ in range(rng.randint(0, 10)):
            a, b = rng.randint(1, n), rng.randint(1, n)
            if a != b:
                es.append((a, b, rng.randint(-3, 9)))
        D = floyd(matrix(n, es, True), n)
        has_neg = any(D[i][i] < 0 for i in range(1, n + 1))
        # 모든 점을 출발점으로 하는 벨만-포드로 음수 사이클과 거리를 따로 구한다
        results = [bellman_ford(n, es, s) for s in range(1, n + 1)]
        bf_neg = any(neg for _, neg in results)
        assert has_neg == bf_neg
        if not has_neg:
            for s in range(1, n + 1):
                assert D[s][1:] == results[s - 1][0][1:]
        else:
            neg_seen += 1
    assert neg_seen > 50
    # 시간: n = 200
    n = 200
    es = [(rng.randint(1, n), rng.randint(1, n), rng.randint(1, 100_000)) for _ in range(n * (n - 1) // 2)]
    D = matrix(n, [(a, b, w) for a, b, w in es if a != b])
    t0 = time.perf_counter()
    floyd(D, n)
    t = time.perf_counter() - t0
    assert t < 20, t
    print(f"n=200: {t:.2f}s, 200^3 = {200 ** 3:,}")
    print("ALL CHECKS PASSED")
