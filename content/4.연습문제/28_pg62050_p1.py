"""지형 이동 (프로그래머스 62050) 풀이와 검증."""
import heapq
import random
import time
from collections import deque
from itertools import combinations

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def solution(land, height):
    N = len(land)
    seen = [[False] * N for _ in range(N)]
    heap = [(0, 0, 0)]                        # (이 칸을 붙이는 비용, 행, 열)
    total = 0
    while heap:
        w, r, c = heapq.heappop(heap)
        if seen[r][c]:
            continue
        seen[r][c] = True
        total += w
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and not seen[nr][nc]:
                diff = abs(land[r][c] - land[nr][nc])
                heapq.heappush(heap, (0 if diff <= height else diff, nr, nc))
    return total


def by_regions(land, height):
    """사다리 없이 오갈 수 있는 칸끼리 BFS로 묶고, 무리 사이 간선으로 크루스칼을 돌린다."""
    N = len(land)
    comp = [[-1] * N for _ in range(N)]
    k = 0
    for sr in range(N):
        for sc in range(N):
            if comp[sr][sc] != -1:
                continue
            comp[sr][sc] = k
            q = deque([(sr, sc)])
            while q:
                r, c = q.popleft()
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N and comp[nr][nc] == -1 \
                            and abs(land[r][c] - land[nr][nc]) <= height:
                        comp[nr][nc] = k
                        q.append((nr, nc))
            k += 1
    edges = []
    for r in range(N):
        for c in range(N):
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if nr < N and nc < N and comp[r][c] != comp[nr][nc]:
                    edges.append((abs(land[r][c] - land[nr][nc]), comp[r][c], comp[nr][nc]))
    parent = list(range(k))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    total = 0
    for w, a, b in sorted(edges):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
            total += w
    return total, k, comp, sorted(set(edges))


def by_all_trees(land, height):
    """칸 그래프(쉬운 이동은 비용 0)의 모든 신장 트리 중 가장 싼 것(아주 작은 땅만)."""
    N = len(land)
    cells = [(r, c) for r in range(N) for c in range(N)]
    idx = {x: i for i, x in enumerate(cells)}
    edges = []
    for r in range(N):
        for c in range(N):
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if nr < N and nc < N:
                    d = abs(land[r][c] - land[nr][nc])
                    edges.append((idx[(r, c)], idx[(nr, nc)], 0 if d <= height else d))
    n = len(cells)
    best = None
    for comb in combinations(edges, n - 1):
        parent = list(range(n))

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
    ex1 = [[1, 4, 8, 10], [5, 5, 5, 5], [10, 10, 10, 10], [10, 10, 10, 20]]
    ex2 = [[10, 11, 10, 11], [2, 21, 20, 10], [1, 20, 21, 11], [2, 1, 2, 1]]
    assert solution(ex1, 3) == 15 == by_regions(ex1, 3)[0]
    assert solution(ex2, 1) == 18 == by_regions(ex2, 1)[0]
    _, k1, comp1, edges1 = by_regions(ex1, 3)
    assert k1 == 3 and comp1 == [[0, 0, 0, 0], [0, 0, 0, 0], [1, 1, 1, 1], [1, 1, 1, 2]]
    assert edges1 == [(5, 0, 1), (10, 1, 2)]               # 무리 사이 가장 싼 사다리 후보
    rng = random.Random(62050)
    for _ in range(300):                                  # 2×2, 3×3에서 모든 신장 트리와 비교
        N = rng.randint(2, 3)
        land = [[rng.randint(1, 9) for _ in range(N)] for _ in range(N)]
        h = rng.randint(1, 4)
        assert solution(land, h) == by_regions(land, h)[0] == by_all_trees(land, h), (land, h)
    for _ in range(500):
        N = rng.randint(4, 8)
        land = [[rng.randint(1, 30) for _ in range(N)] for _ in range(N)]
        h = rng.randint(1, 6)
        assert solution(land, h) == by_regions(land, h)[0], (land, h)
    land = [[rng.randint(1, 10_000) for _ in range(300)] for _ in range(300)]
    t0 = time.perf_counter()
    solution(land, 100)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"300x300: {t:.2f}s")
    print("ALL CHECKS PASSED")
