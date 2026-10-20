"""튜브의 소개팅 (프로그래머스 1839) 풀이와 검증."""
import heapq
import random
import time

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def solution(m, n, s, time_map, trace=None):
    INF = float("inf")
    best = [[INF] * n for _ in range(m)]       # best[r][c]: 이제까지 어느 걸음 수로든 (r, c)에 온 최소 대화 시간
    best[0][0] = 0
    layer = {(0, 0): 0}                        # 정확히 k걸음에 도착한 칸 → 그때의 최소 대화 시간
    k = 0
    while layer:
        if trace is not None:
            trace.append(dict(layer))
        if (m - 1, n - 1) in layer:
            return [k, layer[(m - 1, n - 1)]]
        nxt = {}
        for (r, c), talk in layer.items():
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n and time_map[nr][nc] != -1:
                    t = talk + time_map[nr][nc]
                    if t <= s and t < best[nr][nc] and t < nxt.get((nr, nc), INF):
                        nxt[(nr, nc)] = t      # 더 적은 걸음으로 더 적게 온 적이 있으면 버린다
        for (r, c), t in nxt.items():
            best[r][c] = min(best[r][c], t)
        layer = nxt
        k += 1
    return [-1, -1]


def visit_once(m, n, s, time_map):
    """흔한 실수: 칸마다 처음 도착한 길만 남기는 BFS."""
    seen = {(0, 0)}
    layer = [(0, 0, 0)]
    k = 0
    while layer:
        for r, c, talk in layer:
            if (r, c) == (m - 1, n - 1):
                return [k, talk]
        nxt = []
        for r, c, talk in layer:
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n and time_map[nr][nc] != -1 and (nr, nc) not in seen:
                    t = talk + time_map[nr][nc]
                    if t <= s:
                        seen.add((nr, nc))
                        nxt.append((nr, nc, t))
        layer = nxt
        k += 1
    return [-1, -1]


def cheapest_talk(m, n, time_map):
    """흔한 실수: 대화 시간만 줄이는 다익스트라. [걸음, 대화 시간]을 돌려준다."""
    dist = {(0, 0): (0, 0)}                    # 칸 → (대화 시간, 걸음)
    pq = [(0, 0, 0, 0)]
    while pq:
        talk, steps, r, c = heapq.heappop(pq)
        if dist[(r, c)] != (talk, steps):
            continue
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and time_map[nr][nc] != -1:
                cand = (talk + time_map[nr][nc], steps + 1)
                if cand < dist.get((nr, nc), (float("inf"), 0)):
                    dist[(nr, nc)] = cand
                    heapq.heappush(pq, (*cand, nr, nc))
    talk, steps = dist[(m - 1, n - 1)]
    return [steps, talk]


def count_paths(size):
    """size×size 빈 판에서 겹치지 않는 길의 수."""
    seen = [[False] * size for _ in range(size)]
    seen[0][0] = True
    cnt = 0

    def go(r, c):
        nonlocal cnt
        if r == size - 1 and c == size - 1:
            cnt += 1
            return
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and not seen[nr][nc]:
                seen[nr][nc] = True
                go(nr, nc)
                seen[nr][nc] = False

    go(0, 0)
    return cnt


def by_paths(m, n, s, time_map):
    """겹치지 않는 경로를 모두 만든다(작은 판만)."""
    found = []

    def go(r, c, steps, talk, seen):
        if talk > s:
            return
        if (r, c) == (m - 1, n - 1):
            found.append((steps, talk))
            return
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and time_map[nr][nc] != -1 and (nr, nc) not in seen:
                seen.add((nr, nc))
                go(nr, nc, steps + 1, talk + time_map[nr][nc], seen)
                seen.remove((nr, nc))

    go(0, 0, 0, 0, {(0, 0)})
    return list(min(found)) if found else [-1, -1]


if __name__ == "__main__":
    exs = [
        (3, 3, 150, [[0, 2, 99], [100, 100, 4], [1, 2, 0]], [4, 103]),
        (4, 6, 25, [[0, 1, 1, -1, 2, 4], [-1, 7, 2, 1, 5, 7], [-1, 1, -1, 1, 6, 3], [-1, 1, -1, -1, 7, 0]], [8, 15]),
        (5, 5, 12, [[0, 1, 1, 1, 1], [9, 9, 9, 1, 9], [1, 1, 1, 1, 9], [1, 1, 5, 9, 9], [1, 1, 1, 1, 0]], [12, 11]),
    ]
    for m, n, s, tm, want in exs:
        assert solution(m, n, s, tm) == want == by_paths(m, n, s, tm), (want, solution(m, n, s, tm))
    # 1단계 표: 예시 3의 판에서 s만 바꾼다
    tm3 = exs[2][3]
    for s3, want in [(11, [12, 11]), (12, [12, 11]), (13, [10, 13]), (14, [10, 13]), (15, [8, 15]), (100, [8, 15])]:
        assert solution(5, 5, s3, tm3) == want == by_paths(5, 5, s3, tm3), s3
    assert solution(5, 5, 10, tm3) == [-1, -1]
    # 6단계 추적: 예시 3의 층
    tr = []
    solution(5, 5, 12, tm3, tr)
    assert len(tr) == 13
    assert tr[4] == {(0, 4): 4, (1, 3): 4, (2, 2): 12, (3, 1): 12, (4, 0): 12}
    assert tr[5] == {(2, 3): 5} and tr[6] == {(2, 2): 6}
    assert tr[7] == {(2, 1): 7, (3, 2): 11} and tr[8] == {(2, 0): 8, (3, 1): 8, (4, 2): 12}
    assert tr[9] == {(3, 0): 9, (4, 1): 9} and tr[10] == {(4, 0): 10, (4, 2): 10}
    assert tr[11] == {(4, 3): 11} and tr[12] == {(4, 4): 11}
    # 7단계: 칸마다 한 번만 들르는 BFS는 예시 3에서 틀린다
    assert visit_once(5, 5, 12, tm3) == [-1, -1]
    assert cheapest_talk(5, 5, tm3) == [12, 11] != solution(5, 5, 100, tm3)
    # 2단계: 겹치지 않는 길의 수
    assert [count_paths(k) for k in (4, 5, 6)] == [184, 8512, 1262816]
    rng = random.Random(1839)
    tested = 0
    while tested < 800:
        m, n = rng.randint(2, 4), rng.randint(2, 4)
        tm = [[-1 if rng.random() < 0.2 else rng.randint(0, 9) for _ in range(n)] for _ in range(m)]
        tm[0][0] = tm[m - 1][n - 1] = 0
        s = rng.randint(1, 30)
        want = by_paths(m, n, s, tm)
        if want == [-1, -1]:
            continue
        assert solution(m, n, s, tm) == want, (m, n, s, tm)
        tested += 1
    # 50×50 판: 작은 값, 아주 큰 값(2^31 − 1 이하), 벽이 섞인 판, 한 줄로 구불구불한 판
    boards = []
    tm = [[rng.randint(0, 5) for _ in range(50)] for _ in range(50)]
    boards += [(10 ** 9, tm), (60, tm)]
    for _ in range(10):
        boards.append((2 ** 31 - 1, [[rng.randint(0, 2 ** 31 - 1) for _ in range(50)] for _ in range(50)]))
        boards.append((rng.randint(100, 3000), [[-1 if rng.random() < 0.3 else rng.randint(0, 100) for _ in range(50)] for _ in range(50)]))
    snake = [[0] * 50 for _ in range(50)]
    for r in range(1, 50, 2):
        snake[r] = [-1] * 50
        snake[r][49 if r % 4 == 1 else 0] = 0
    boards.append((1, snake))
    t0 = time.perf_counter()
    for sb, tm in boards:
        tm[0][0] = tm[49][49] = 0
        solution(50, 50, sb, tm)
    t = time.perf_counter() - t0
    assert solution(50, 50, 1, snake) == [1274, 0]
    assert t < 20, t
    print(f"50x50 판 {len(boards)}개: {t:.2f}s")
    print("ALL CHECKS PASSED")
