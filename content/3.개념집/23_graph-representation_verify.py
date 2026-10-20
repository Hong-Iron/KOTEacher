"""23.그래프 표현: 간선 목록, 인접 리스트, 인접 행렬, 격자를 만들고 서로 맞는지 확인한다."""
import random
from collections import deque

INF = float("inf")


def to_adj_list(n, edges, directed=False):
    g = [[] for _ in range(n + 1)]          # 0번은 비워 두고 1 ~ n을 쓴다
    for a, b, w in edges:
        g[a].append((b, w))
        if not directed:
            g[b].append((a, w))
    return g


def to_matrix(n, edges, directed=False):
    M = [[INF] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        M[i][i] = 0
    for a, b, w in edges:
        M[a][b] = min(M[a][b], w)
        if not directed:
            M[b][a] = min(M[b][a], w)
    return M


def grid_neighbors(grid, r, c):
    R, C = len(grid), len(grid[0])
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < R and 0 <= nc < C and grid[nr][nc] == 0:
            yield nr, nc


def reach(n, g, s):
    seen, q = {s}, deque([s])
    while q:
        v = q.popleft()
        for u, _ in g[v]:
            if u not in seen:
                seen.add(u)
                q.append(u)
    return seen


if __name__ == "__main__":
    edges = [(1, 2, 5), (1, 3, 2), (2, 4, 1), (3, 4, 7)]
    g = to_adj_list(4, edges)
    assert g == [[], [(2, 5), (3, 2)], [(1, 5), (4, 1)], [(1, 2), (4, 7)], [(2, 1), (3, 7)]]
    M = to_matrix(4, edges)
    assert M[1][1:] == [0, 5, 2, INF] and M[4][1:] == [INF, 1, 7, 0]
    assert sum(len(x) for x in g) == 2 * len(edges)          # 차수의 합 = 2m
    # C1: 방향 간선 [1,2], [2,3], [3,1], [3,4]
    d = to_adj_list(4, [(1, 2, 1), (2, 3, 1), (3, 1, 1), (3, 4, 1)], directed=True)
    assert [[u for u, _ in x] for x in d] == [[], [2], [3], [1, 4], []]
    # C3: 양방향인데 한쪽만 넣으면 1에서 2로 못 간다
    one_way = to_adj_list(2, [(2, 1, 1)], directed=True)
    assert 2 not in reach(2, one_way, 1) and 2 in reach(2, to_adj_list(2, [(2, 1, 1)]), 1)
    # 격자: 모서리 2, 가장자리 3, 안쪽 4
    grid = [[0] * 4 for _ in range(3)]
    assert [len(list(grid_neighbors(grid, r, c))) for r, c in ((0, 0), (0, 1), (1, 1))] == [2, 3, 4]
    # 무작위: 세 표현이 같은 그래프를 나타낸다
    rng = random.Random(23)
    for _ in range(1000):
        n = rng.randint(1, 8)
        es = []
        for _ in range(rng.randint(0, 12)):
            a, b = rng.randint(1, n), rng.randint(1, n)
            if a != b:
                es.append((a, b, rng.randint(1, 9)))
        directed = rng.random() < 0.5
        g, M = to_adj_list(n, es, directed), to_matrix(n, es, directed)
        for a in range(1, n + 1):
            for b in range(1, n + 1):
                if a != b:
                    ws = [w for u, w in g[a] if u == b]
                    assert (min(ws) if ws else INF) == M[a][b]
    assert 100_000 ** 2 == 10 ** 10
    same = [[]] * 3                                  # 모든 칸이 같은 리스트
    same[0].append(1)
    assert same[1] == [1] and [[] for _ in range(3)][1] == []
    print("ALL CHECKS PASSED")
