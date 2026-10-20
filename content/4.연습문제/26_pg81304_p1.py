"""미로 탈출 (프로그래머스 81304) 풀이와 검증."""
import heapq
import random
import time


def solution(n, start, end, roads, traps, seen=None):
    tid = {t: i for i, t in enumerate(traps)}          # 함정 번호 → 비트 자리
    adj = [[] for _ in range(n + 1)]
    for p, q, s in roads:
        adj[p].append((q, s, True))                    # 원래 방향 p → q
        adj[q].append((p, s, False))                   # 뒤집혔을 때만 쓰는 q → p

    def on(v, mask):                                   # v가 함정이고 지금 켜져(뒤집혀) 있나
        return v in tid and (mask >> tid[v]) & 1

    INF = float("inf")
    dist = {(start, 0): 0}
    heap = [(0, start, 0)]
    while heap:
        d, v, mask = heapq.heappop(heap)
        if d > dist[(v, mask)]:
            continue
        if seen is not None:
            seen[(v, mask)] = d
        if v == end:
            return d
        for u, w, forward in adj[v]:
            flipped = on(v, mask) != on(u, mask)       # 둘 중 하나만 켜져 있으면 길이 뒤집힌 상태
            if forward == flipped:                     # 원래 길은 안 뒤집혔을 때, 반대 길은 뒤집혔을 때만
                continue
            nmask = mask ^ (1 << tid[u]) if u in tid else mask   # 함정에 들어가면 켜고 끈다
            nd = d + w
            if nd < dist.get((u, nmask), INF):
                dist[(u, nmask)] = nd
                heapq.heappush(heap, (nd, u, nmask))
    return -1


def by_literal(n, start, end, roads, traps):
    """길마다 지금 방향을 그대로 들고 다니는 풀이(작은 입력만)."""
    trapset = set(traps)
    INF = float("inf")
    init = tuple((p, q) for p, q, _ in roads)
    dist = {(start, init): 0}
    heap = [(0, start, init)]
    while heap:
        d, v, dirs = heapq.heappop(heap)
        if d > dist[(v, dirs)]:
            continue
        if v == end:
            return d
        for i, (a, b) in enumerate(dirs):
            if a != v:
                continue
            u = b
            nd = d + roads[i][2]
            if u in trapset:                           # u에 붙은 길을 모두 뒤집는다
                ndirs = tuple((y, x) if u in (x, y) else (x, y) for x, y in dirs)
            else:
                ndirs = dirs
            if nd < dist.get((u, ndirs), INF):
                dist[(u, ndirs)] = nd
                heapq.heappush(heap, (nd, u, ndirs))
    return -1


if __name__ == "__main__":
    assert solution(3, 1, 3, [[1, 2, 2], [3, 2, 3]], [2]) == 5 == by_literal(3, 1, 3, [[1, 2, 2], [3, 2, 3]], [2])
    ex2 = (4, 1, 4, [[1, 2, 1], [3, 2, 1], [2, 4, 1]], [2, 3])
    assert solution(*ex2) == 4 == by_literal(*ex2)
    got = {}
    solution(*ex2, seen=got)                          # 함정 2는 1번째 비트, 3은 2번째 비트
    assert got[(1, 0b00)] == 0 and got[(2, 0b01)] == 1 and got[(3, 0b11)] == 2
    assert got[(2, 0b10)] == 3 and got[(4, 0b10)] == 4 and got[(1, 0b01)] == 2
    rng = random.Random(81304)
    tested = 0
    while tested < 800:
        n = rng.randint(2, 5)
        roads = []
        for _ in range(rng.randint(1, 6)):
            p, q = rng.sample(range(1, n + 1), 2)
            roads.append([p, q, rng.randint(1, 9)])
        start, end = rng.sample(range(1, n + 1), 2)
        others = [v for v in range(1, n + 1) if v not in (start, end)]
        traps = rng.sample(others, rng.randint(0, len(others)))
        want = by_literal(n, start, end, roads, traps)
        if want == -1:
            continue
        assert solution(n, start, end, roads, traps) == want, (n, start, end, roads, traps)
        tested += 1
    # 방 1,000개, 길 3,000개, 함정 10개. 도착 방으로 가는 길을 비싼 길 하나로 두어 거의 모든 상태를 돌게 한다
    n = 1000
    roads = [[v, v + 1, 1] for v in range(1, n - 1)] + [[v + 1, v, 1] for v in range(1, n - 1)]
    while len(roads) < 2999:
        p, q = rng.sample(range(1, n), 2)
        roads.append([p, q, 1])
    roads.append([1, n, 3000])
    traps = rng.sample(range(2, n), 10)
    t0 = time.perf_counter()
    assert solution(n, 1, n, roads, traps) == 3000
    t = time.perf_counter() - t0
    assert t < 20, t
    print(f"n=1000, 3000 roads, 10 traps: {t:.2f}s")
    print("ALL CHECKS PASSED")
