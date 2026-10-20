"""24.너비 우선 탐색(BFS): 인접 리스트·격자 BFS와 문서 주장의 확인."""
import random
import time
from collections import deque


def bfs(graph, s):
    """graph[v]: v의 이웃 목록. 돌려주는 dist[v]: s에서 v까지 간선 수의 최솟값, 못 가면 -1."""
    dist = [-1] * len(graph)
    dist[s] = 0
    q = deque([s])
    while q:
        v = q.popleft()
        for u in graph[v]:
            if dist[u] == -1:              # 처음 발견했을 때 바로 표시한다
                dist[u] = dist[v] + 1
                q.append(u)
    return dist


def bfs_checked(graph, s):
    """매 바퀴 큐 안의 거리가 앞에서 뒤로 줄지 않고, 차이가 1 이하인지 확인하며 돈다."""
    dist = [-1] * len(graph)
    dist[s] = 0
    q = deque([s])
    while q:
        ds = [dist[x] for x in q]
        assert all(a <= b for a, b in zip(ds, ds[1:])) and ds[-1] - ds[0] <= 1
        v = q.popleft()
        for u in graph[v]:
            if dist[u] == -1:
                dist[u] = dist[v] + 1
                q.append(u)
    return dist


def bfs_grid(maze, sr, sc):
    R, C = len(maze), len(maze[0])
    dist = [[-1] * C for _ in range(R)]
    dist[sr][sc] = 0
    q = deque([(sr, sc)])
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and maze[nr][nc] != "#" and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                q.append((nr, nc))
    return dist


def multi_source(maze, sources):
    R, C = len(maze), len(maze[0])
    dist = [[-1] * C for _ in range(R)]
    q = deque()
    for r, c in sources:
        dist[r][c] = 0
        q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and maze[nr][nc] != "#" and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                q.append((nr, nc))
    return dist


def mark_on_pop(graph, s):
    """흔한 잘못: 꺼낼 때 방문 표시를 하고, 넣을 때마다 거리를 덮어쓴다."""
    visited = [False] * len(graph)
    dist = [-1] * len(graph)
    dist[s] = 0
    q = deque([s])
    while q:
        v = q.popleft()
        visited[v] = True
        for u in graph[v]:
            if not visited[u]:
                dist[u] = dist[v] + 1
                q.append(u)
    return dist


def shortest_by_relax(graph, s):
    """간선마다 '거리 + 1'로 줄이기를 n번 되풀이한다(BFS와 다른 방법)."""
    n = len(graph)
    INF = float("inf")
    d = [INF] * n
    d[s] = 0
    for _ in range(n):
        for v in range(n):
            for u in graph[v]:
                if d[v] + 1 < d[u]:
                    d[u] = d[v] + 1
    return [x if x != INF else -1 for x in d]


def undirected(n, edges):
    g = [[] for _ in range(n)]
    for a, b in edges:
        g[a].append(b)
        g[b].append(a)
    for x in g:
        x.sort()
    return g


if __name__ == "__main__":
    # 예시로 보기: 미로
    maze = ["S.#.",
            "....",
            "#.#.",
            "...G"]
    d = bfs_grid(maze, 0, 0)
    assert d == [[0, 1, -1, 5], [1, 2, 3, 4], [-1, 3, -1, 5], [5, 4, 5, 6]]
    # 예시의 큐 추적(앞 여섯 번)
    R, C = 4, 4
    dist = [[-1] * C for _ in range(R)]
    dist[0][0] = 0
    q, rows = deque([(0, 0)]), []
    while q and len(rows) < 6:
        r, c = q.popleft()
        added = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < C and maze[nr][nc] != "#" and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                q.append((nr, nc))
                added.append((nr, nc))
        rows.append(((r, c), dist[r][c], added, list(q)))
    assert rows == [
        ((0, 0), 0, [(1, 0), (0, 1)], [(1, 0), (0, 1)]),
        ((1, 0), 1, [(1, 1)], [(0, 1), (1, 1)]),
        ((0, 1), 1, [], [(1, 1)]),
        ((1, 1), 2, [(2, 1), (1, 2)], [(2, 1), (1, 2)]),
        ((2, 1), 3, [(3, 1)], [(1, 2), (3, 1)]),
        ((1, 2), 3, [(1, 3)], [(3, 1), (1, 3)]),
    ]
    # C1: 점 1 ~ 6
    g1 = undirected(7, [(1, 2), (1, 3), (2, 4), (3, 4), (3, 5), (4, 6), (5, 6)])
    assert bfs(g1, 1)[1:] == [0, 1, 1, 2, 2, 3]
    # C2: 여러 출발점 BFS = 출발점마다 BFS를 한 뒤 가장 작은 값
    m2 = ["....", ".#..", "...."]
    ms = multi_source(m2, [(0, 0), (2, 3)])
    one = [bfs_grid(m2, 0, 0), bfs_grid(m2, 2, 3)]
    assert all(ms[r][c] == min(x[r][c] for x in one) for r in range(3) for c in range(4) if m2[r][c] != "#")
    # 오해: 꺼낼 때 표시하면 거리가 덮어써진다 (s=0, a=1, b=2, w=3, u=4)
    gm = undirected(5, [(0, 1), (0, 2), (1, 3), (2, 4), (3, 4)])
    assert bfs(gm, 0)[4] == 2 and mark_on_pop(gm, 0)[4] == 3
    # C4: 가중치가 있으면 간선이 적은 길이 싸다는 보장이 없다 (A=0, B=1, C=2)
    wedges = {(0, 1): 10, (0, 2): 1, (2, 1): 1}
    gw = undirected(3, list(wedges))
    assert bfs(gw, 0)[1] == 1                          # 간선 1개: A-B, 비용 10
    assert min(wedges[(0, 1)], wedges[(0, 2)] + wedges[(2, 1)]) == 2
    # 무작위: BFS = 줄이기 반복, 큐 불변식 확인
    rng = random.Random(24)
    for _ in range(2000):
        n = rng.randint(1, 9)
        es = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 14))]
        es = [(a, b) for a, b in es if a != b]
        directed = rng.random() < 0.5
        g = [[] for _ in range(n)]
        for a, b in es:
            g[a].append(b)
            if not directed:
                g[b].append(a)
        s = rng.randrange(n)
        assert bfs_checked(g, s) == bfs(g, s) == shortest_by_relax(g, s)
    # 시간: 점 20만 개, 간선 40만 개
    n = 200_000
    g = [[] for _ in range(n)]
    for _ in range(400_000):
        a, b = rng.randrange(n), rng.randrange(n)
        g[a].append(b)
        g[b].append(a)
    t0 = time.perf_counter()
    bfs(g, 0)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"n=200k, m=400k: {t:.2f}s")
    print("ALL CHECKS PASSED")
