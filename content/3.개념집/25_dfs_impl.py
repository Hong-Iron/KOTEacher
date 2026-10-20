"""25.깊이 우선 탐색(DFS): 재귀·스택 DFS, 연결 덩어리, 방향 그래프의 사이클 판정 확인."""
import random
import sys
from collections import deque


def dfs_order(graph, s, seen=None, out=None):
    if seen is None:
        seen, out = set(), []
    seen.add(s)
    out.append(s)
    for u in graph[s]:
        if u not in seen:
            dfs_order(graph, u, seen, out)
    return out


def dfs_order_stack(graph, s):
    """재귀와 같은 순서가 나오도록: 꺼낼 때 표시하고, 이웃을 거꾸로 넣는다."""
    seen, out, stack = set(), [], [s]
    while stack:
        v = stack.pop()
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
        for u in reversed(graph[v]):
            if u not in seen:
                stack.append(u)
    return out


def count_components(n, graph):
    seen, cnt = [False] * n, 0
    for s in range(n):
        if not seen[s]:
            cnt += 1
            stack = [s]
            seen[s] = True
            while stack:
                v = stack.pop()
                for u in graph[v]:
                    if not seen[u]:
                        seen[u] = True
                        stack.append(u)
    return cnt


def has_cycle(n, graph):
    """0: 아직, 1: 탐색 중(회색), 2: 끝남(검정). 회색을 다시 만나면 사이클."""
    color = [0] * n

    def go(v):
        color[v] = 1
        for u in graph[v]:
            if color[u] == 1:
                return True
            if color[u] == 0 and go(u):
                return True
        color[v] = 2
        return False

    return any(color[v] == 0 and go(v) for v in range(n))


def has_cycle_visited_only(n, graph):
    """잘못된 판정: 이미 방문한 점을 다시 만나면 사이클이라고 본다."""
    seen = [False] * n

    def go(v):
        seen[v] = True
        for u in graph[v]:
            if seen[u] or go(u):
                return True
        return False

    return any(not seen[v] and go(v) for v in range(n))


def has_cycle_kahn(n, graph):
    indeg = [0] * n
    for v in range(n):
        for u in graph[v]:
            indeg[u] += 1
    q = deque(v for v in range(n) if indeg[v] == 0)
    done = 0
    while q:
        v = q.popleft()
        done += 1
        for u in graph[v]:
            indeg[u] -= 1
            if indeg[u] == 0:
                q.append(u)
    return done < n


def undirected(n, edges):
    g = [[] for _ in range(n)]
    for a, b in edges:
        g[a].append(b)
        g[b].append(a)
    for x in g:
        x.sort()
    return g


if __name__ == "__main__":
    # 예시로 보기: 1–2, 1–3, 2–4, 4–5, 3–5, 6–7
    g = undirected(8, [(1, 2), (1, 3), (2, 4), (4, 5), (3, 5), (6, 7)])
    assert dfs_order(g, 1) == [1, 2, 4, 5, 3] == dfs_order_stack(g, 1)
    assert count_components(8, g) - 1 == 2                       # 0번 칸은 쓰지 않아 따로 하나로 센다
    # C1: 1–2, 1–5, 2–3, 2–4, 5–6
    c1 = undirected(7, [(1, 2), (1, 5), (2, 3), (2, 4), (5, 6)])
    assert dfs_order(c1, 1) == [1, 2, 3, 4, 5, 6]
    seen, q, bfs_order = {1}, deque([1]), []
    while q:
        v = q.popleft()
        bfs_order.append(v)
        for u in c1[v]:
            if u not in seen:
                seen.add(u)
                q.append(u)
    assert bfs_order == [1, 2, 5, 3, 4, 6]
    # C3: 다이아몬드 a→b, a→c, b→d, c→d (0, 1, 2, 3)는 사이클이 없다
    diamond = [[1, 2], [3], [3], []]
    assert not has_cycle(4, diamond) and has_cycle_visited_only(4, diamond)
    assert has_cycle(3, [[1], [2], [0]])
    # 무작위: 재귀 순서 = 스택 순서, 덩어리 수 = BFS, 회색 판정 = 칸 판정(위상 정렬)
    rng = random.Random(25)
    for _ in range(2000):
        n = rng.randint(1, 9)
        es = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 12))]
        es = [(a, b) for a, b in es if a != b]
        ug = undirected(n, es)
        s = rng.randrange(n)
        assert dfs_order(ug, s) == dfs_order_stack(ug, s)
        # BFS로 덩어리 수
        seen, comps = set(), 0
        for v in range(n):
            if v not in seen:
                comps += 1
                q = deque([v])
                seen.add(v)
                while q:
                    x = q.popleft()
                    for y in ug[x]:
                        if y not in seen:
                            seen.add(y)
                            q.append(y)
        assert count_components(n, ug) == comps
        dg = [[] for _ in range(n)]
        for a, b in es:
            dg[a].append(b)
        assert has_cycle(n, dg) == has_cycle_kahn(n, dg)
    # 재귀 DFS는 한 줄로 이어진 점 2,000개에서 기본 재귀 한도(1,000)에 걸린다
    line = [[i + 1] if i + 1 < 2000 else [] for i in range(2000)]
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)
    try:
        dfs_order(line, 0)
        raise AssertionError("RecursionError가 나야 한다")
    except RecursionError:
        pass
    sys.setrecursionlimit(old)
    assert len(dfs_order_stack(line, 0)) == 2000
    print("ALL CHECKS PASSED")
