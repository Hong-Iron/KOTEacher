"""경주로 건설 (프로그래머스 67259) 풀이와 검증."""
import heapq
import random

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def solution(board):
    N = len(board)
    INF = float("inf")
    cost = [[[INF] * 4 for _ in range(N)] for _ in range(N)]   # cost[r][c][들어온 방향]
    heap = []
    for d, (dr, dc) in enumerate(DIRS):                        # 첫 걸음은 방향 상관없이 100
        r, c = dr, dc
        if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
            cost[r][c][d] = 100
            heapq.heappush(heap, (100, r, c, d))
    while heap:
        w, r, c, d = heapq.heappop(heap)
        if w > cost[r][c][d]:
            continue
        for nd, (dr, dc) in enumerate(DIRS):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                nw = w + (100 if nd == d else 600)             # 꺾으면 코너 500원 더
                if nw < cost[nr][nc][nd]:
                    cost[nr][nc][nd] = nw
                    heapq.heappush(heap, (nw, nr, nc, nd))
    return min(cost[N - 1][N - 1])


def by_relax(board):
    """상태 (칸, 방향)마다 비용을 '더 줄지 않을 때까지' 되풀이해 줄인다(다익스트라 없이)."""
    N = len(board)
    INF = float("inf")
    cost = {}
    for d, (dr, dc) in enumerate(DIRS):
        if 0 <= dr < N and 0 <= dc < N and board[dr][dc] == 0:
            cost[(dr, dc, d)] = 100
    changed = True
    while changed:
        changed = False
        for (r, c, d), w in list(cost.items()):
            for nd, (dr, dc) in enumerate(DIRS):
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    nw = w + (100 if nd == d else 600)
                    if nw < cost.get((nr, nc, nd), INF):
                        cost[(nr, nc, nd)] = nw
                        changed = True
    return min(cost.get((N - 1, N - 1, d), INF) for d in range(4))


def by_paths(board):
    """겹치지 않는 칸 경로를 모두 만들고 '직선 100원, 코너 500원'으로 센다(작은 판만)."""
    N = len(board)
    best = [float("inf")]

    def go(r, c, d, w, seen):
        if w >= best[0]:
            return
        if (r, c) == (N - 1, N - 1):
            best[0] = w
            return
        for nd, (dr, dc) in enumerate(DIRS):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0 and (nr, nc) not in seen:
                seen.add((nr, nc))
                go(nr, nc, nd, w + 100 + (500 if d is not None and nd != d else 0), seen)
                seen.remove((nr, nc))

    go(0, 0, None, 0, {(0, 0)})
    return best[0]


def one_cost_per_cell(board):
    """칸마다 비용 하나만 기억하는 흔한 잘못."""
    N = len(board)
    INF = float("inf")
    cost = [[INF] * N for _ in range(N)]
    cost[0][0] = 0
    heap = [(0, 0, 0, -1)]
    while heap:
        w, r, c, d = heapq.heappop(heap)
        if w > cost[r][c]:
            continue
        for nd, (dr, dc) in enumerate(DIRS):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                nw = w + (100 if d in (-1, nd) else 600)
                if nw < cost[nr][nc]:
                    cost[nr][nc] = nw
                    heapq.heappush(heap, (nw, nr, nc, nd))
    return cost[N - 1][N - 1]


if __name__ == "__main__":
    exs = [
        ([[0, 0, 0], [0, 0, 0], [0, 0, 0]], 900),
        ([[0, 0, 0, 0, 0, 0, 0, 1], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0],
          [0, 0, 0, 1, 0, 0, 0, 1], [0, 0, 1, 0, 0, 0, 1, 0], [0, 1, 0, 0, 0, 1, 0, 0], [1, 0, 0, 0, 0, 0, 0, 0]], 3800),
        ([[0, 0, 1, 0], [0, 0, 0, 0], [0, 1, 0, 1], [1, 0, 0, 0]], 2100),
        ([[0, 0, 0, 0, 0, 0], [0, 1, 1, 1, 1, 0], [0, 0, 1, 0, 0, 0], [1, 0, 0, 1, 0, 1], [0, 1, 0, 0, 0, 1],
          [0, 0, 0, 0, 0, 0]], 3200),
    ]
    for b, want in exs:
        assert solution(b) == want == by_relax(b), (b, want)
    # 6단계 추적: 반례 판의 (칸, 들어온 방향)별 최소 비용. 방향 번호: 0 아래, 1 위, 2 오른쪽, 3 왼쪽
    def all_costs(board):
        N = len(board)
        INF = float("inf")
        cost = [[[INF] * 4 for _ in range(N)] for _ in range(N)]
        heap = []
        for d, (dr, dc) in enumerate(DIRS):
            if 0 <= dr < N and 0 <= dc < N and board[dr][dc] == 0:
                cost[dr][dc][d] = 100
                heapq.heappush(heap, (100, dr, dc, d))
        while heap:
            w, r, c, d = heapq.heappop(heap)
            if w > cost[r][c][d]:
                continue
            for nd, (dr, dc) in enumerate(DIRS):
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    nw = w + (100 if nd == d else 600)
                    if nw < cost[nr][nc][nd]:
                        cost[nr][nc][nd] = nw
                        heapq.heappush(heap, (nw, nr, nc, nd))
        return cost
    cc = all_costs([[0, 0, 1], [0, 0, 0], [0, 1, 0]])
    assert (cc[1][0][0], cc[0][1][2], cc[1][1][0], cc[1][1][2], cc[1][2][2], cc[2][2][0]) == (100, 100, 700, 700, 800, 1400)
    assert cc[1][1][0] + 600 == 1300 > cc[1][2][2]
    # 무작위: 다익스트라 = 줄이기 반복 = 칸 경로 전수(작은 판)
    rng = random.Random(67259)
    tested = 0
    while tested < 600:
        N = rng.randint(3, 5)
        b = [[1 if rng.random() < 0.25 else 0 for _ in range(N)] for _ in range(N)]
        b[0][0] = b[N - 1][N - 1] = 0
        ans = solution(b)
        if ans == float("inf"):
            continue
        assert ans == by_relax(b) == by_paths(b), b
        tested += 1
    # 칸마다 비용 하나만 기억하면 틀리는 판
    bad = [[0, 0, 1], [0, 0, 0], [0, 1, 0]]
    assert solution(bad) == 1400 == by_paths(bad) and one_cost_per_cell(bad) == 1900
    assert one_cost_per_cell(exs[2][0]) != exs[2][1]                  # 예시 3번도 틀린다
    print("ALL CHECKS PASSED")
