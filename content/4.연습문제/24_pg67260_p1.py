"""동굴 탐험 (프로그래머스 67260) 풀이와 검증."""
import random
import time
from collections import deque
from itertools import permutations


def solution(n, path, order, trace=None):
    graph = [[] for _ in range(n)]
    for a, b in path:
        graph[a].append(b)
        graph[b].append(a)
    succ = [[] for _ in range(n)]              # "먼저 → 나중" 간선
    indeg = [0] * n
    parent = [-1] * n                          # 0번 방을 뿌리로 한 부모: 부모를 먼저 가야 자식에 간다
    parent[0] = 0
    q = deque([0])
    while q:
        v = q.popleft()
        for u in graph[v]:
            if parent[u] == -1:
                parent[u] = v
                succ[v].append(u)
                indeg[u] += 1
                q.append(u)
    for a, b in order:                         # a를 먼저 가야 b에 간다
        succ[a].append(b)
        indeg[b] += 1
    q = deque(v for v in range(n) if indeg[v] == 0)
    done = 0
    while q:                                   # 위상 정렬(칸 방식)
        v = q.popleft()
        done += 1
        if trace is not None:
            trace.append(v)
        for u in succ[v]:
            indeg[u] -= 1
            if indeg[u] == 0:
                q.append(u)
    return done == n                           # 모두 뗄 수 있으면 사이클이 없다


def by_waiting(n, path, order):
    """실제로 돌아다니며, 먼저 가야 할 방을 아직 안 간 방은 '대기'로 두는 풀이."""
    graph = [[] for _ in range(n)]
    for a, b in path:
        graph[a].append(b)
        graph[b].append(a)
    need, unlock = {}, {}
    for a, b in order:
        need[b] = a
        unlock[a] = b
    if 0 in need:
        return False
    visited = [False] * n
    waiting = set()
    visited[0] = True
    q = deque([0])
    cnt = 1
    while q:
        v = q.popleft()
        if v in unlock:
            w = unlock[v]
            if w in waiting:                   # 기다리던 방을 이제 갈 수 있다
                waiting.discard(w)
                visited[w] = True
                cnt += 1
                q.append(w)
        for u in graph[v]:
            if visited[u]:
                continue
            if u in need and not visited[need[u]]:
                waiting.add(u)                 # 닿았지만 아직 들어갈 수 없다
                continue
            visited[u] = True
            cnt += 1
            q.append(u)
    return cnt == n


def by_permutations(n, path, order):
    """방을 처음 방문하는 순서를 모두 해 본다(방 7개 이하)."""
    graph = [[] for _ in range(n)]
    for a, b in path:
        graph[a].append(b)
        graph[b].append(a)
    parent = [-1] * n
    parent[0] = 0
    q = deque([0])
    while q:
        v = q.popleft()
        for u in graph[v]:
            if parent[u] == -1:
                parent[u] = v
                q.append(u)
    for perm in permutations(range(1, n)):
        pos = {0: 0}
        for i, v in enumerate(perm):
            pos[v] = i + 1
        if all(pos[parent[v]] < pos[v] for v in range(1, n)) and all(pos[a] < pos[b] for a, b in order):
            return True
    return False


def random_case(rng, n):
    path = [[rng.randrange(v), v] for v in range(1, n)]
    rooms = list(range(n))
    rng.shuffle(rooms)
    k = rng.randint(1, n // 2)
    order = [[rooms[2 * i], rooms[2 * i + 1]] for i in range(k)]   # 방마다 순서 쌍에 한 번만 나온다
    return path, order


if __name__ == "__main__":
    P1 = [[0, 1], [0, 3], [0, 7], [8, 1], [3, 6], [1, 2], [4, 7], [7, 5]]
    assert solution(9, P1, [[8, 5], [6, 7], [4, 1]]) is True
    assert solution(9, [[8, 1], [0, 1], [1, 2], [0, 7], [4, 7], [0, 3], [7, 5], [3, 6]], [[4, 1], [5, 2]]) is True
    assert solution(9, P1, [[4, 1], [8, 7], [6, 5]]) is False
    assert solution(3, [[0, 1], [1, 2]], [[2, 1]]) is False == by_permutations(3, [[0, 1], [1, 2]], [[2, 1]])
    for args in ((9, P1, [[8, 5], [6, 7], [4, 1]]), (9, P1, [[4, 1], [8, 7], [6, 5]])):
        assert solution(*args) == by_waiting(*args)
    # 6단계: 예시 3의 사이클 1 → 8(통로) → 7(순서) → 4(통로) → 1(순서)
    parent = {1: 0, 3: 0, 7: 0, 8: 1, 6: 3, 2: 1, 4: 7, 5: 7}
    tree_edges = {(p, c) for c, p in parent.items()}
    order_edges = {(4, 1), (8, 7), (6, 5)}
    assert {(1, 8), (7, 4)} <= tree_edges and {(8, 7), (4, 1)} <= order_edges
    # 예시 1의 위상 정렬 순서(칸 방식, 큐)
    succ = {v: [] for v in range(9)}
    indeg = [0] * 9
    for c, p in parent.items():
        succ[p].append(c)
        indeg[c] += 1
    for a, b in [[8, 5], [6, 7], [4, 1]]:
        succ[a].append(b)
        indeg[b] += 1
    assert [v for v in range(9) if indeg[v] == 0] == [0]
    tr = []
    assert solution(9, P1, [[8, 5], [6, 7], [4, 1]], tr) and tr == [0, 3, 6, 7, 4, 1, 8, 2, 5], tr
    tr3 = []
    assert not solution(9, P1, [[4, 1], [8, 7], [6, 5]], tr3) and tr3 == [0, 3, 6], tr3
    rng = random.Random(67260)
    for _ in range(2000):
        n = rng.randint(2, 7)
        path, order = random_case(rng, n)
        a = solution(n, path, order)
        assert a == by_waiting(n, path, order) == by_permutations(n, path, order), (n, path, order)
    for _ in range(300):
        n = rng.randint(8, 60)
        path, order = random_case(rng, n)
        assert solution(n, path, order) == by_waiting(n, path, order)
    n = 200_000
    path, order = random_case(rng, n)
    t0 = time.perf_counter()
    solution(n, path, order)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"n=200k: {t:.2f}s")
    print("ALL CHECKS PASSED")
