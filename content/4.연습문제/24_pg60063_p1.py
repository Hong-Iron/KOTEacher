"""블록 이동하기 (프로그래머스 60063) 풀이와 검증."""
import random
from collections import deque


def solution(board):
    N = len(board)
    B = [[1] * (N + 2)] + [[1] + row + [1] for row in board] + [[1] * (N + 2)]   # 벽으로 한 겹 두른다

    def nexts(a, b):
        (r1, c1), (r2, c2) = a, b
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):            # 평행 이동
            if B[r1 + dr][c1 + dc] == 0 and B[r2 + dr][c2 + dc] == 0:
                yield tuple(sorted(((r1 + dr, c1 + dc), (r2 + dr, c2 + dc))))
        if r1 == r2:                                                  # 가로 → 세로
            for d in (-1, 1):
                if B[r1 + d][c1] == 0 and B[r2 + d][c2] == 0:
                    yield tuple(sorted(((r1, c1), (r1 + d, c1))))
                    yield tuple(sorted(((r2, c2), (r2 + d, c2))))
        else:                                                         # 세로 → 가로
            for d in (-1, 1):
                if B[r1][c1 + d] == 0 and B[r2][c2 + d] == 0:
                    yield tuple(sorted(((r1, c1), (r1, c1 + d))))
                    yield tuple(sorted(((r2, c2), (r2, c2 + d))))

    start = ((1, 1), (1, 2))
    dist = {start: 0}
    q = deque([start])
    while q:
        a, b = q.popleft()
        if (N, N) in (a, b):
            return dist[(a, b)]
        for nxt in nexts(a, b):
            if nxt not in dist:
                dist[nxt] = dist[(a, b)] + 1
                q.append(nxt)
    return -1


def by_vectors(board):
    """회전을 '축 A를 중심으로 B를 90도 돌린다'로 직접 계산하는 다른 풀이(0부터 센 좌표)."""
    N = len(board)

    def free(p):
        r, c = p
        return 0 <= r < N and 0 <= c < N and board[r][c] == 0

    def moves(s):
        a, b = s
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            na, nb = (a[0] + dr, a[1] + dc), (b[0] + dr, b[1] + dc)
            if free(na) and free(nb):
                yield frozenset((na, nb))
        for axis, other in ((a, b), (b, a)):
            vr, vc = other[0] - axis[0], other[1] - axis[1]
            for rr, rc in ((-vc, vr), (vc, -vr)):                    # 90도 두 방향
                new = (axis[0] + rr, axis[1] + rc)
                diag = (other[0] + rr, other[1] + rc)                # 돌며 쓸고 지나가는 칸
                if free(new) and free(diag):
                    yield frozenset((axis, new))

    start = frozenset(((0, 0), (0, 1)))
    seen, q = {start: 0}, deque([start])
    while q:
        s = q.popleft()
        if (N - 1, N - 1) in s:
            return seen[s]
        a, b = tuple(s)
        for t in moves((a, b)):
            if t not in seen:
                seen[t] = seen[s] + 1
                q.append(t)
    return -1


def path_of(board):
    """최단 경로 하나를 (0부터 센 좌표로) 돌려준다."""
    N = len(board)

    def free(p):
        return 0 <= p[0] < N and 0 <= p[1] < N and board[p[0]][p[1]] == 0

    start = ((0, 0), (0, 1))
    par, q = {start: None}, deque([start])
    while q:
        s = q.popleft()
        if (N - 1, N - 1) in s:
            out = []
            while s:
                out.append(s)
                s = par[s]
            return out[::-1]
        a, b = s
        cand = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            na, nb = (a[0] + dr, a[1] + dc), (b[0] + dr, b[1] + dc)
            if free(na) and free(nb):
                cand.append(tuple(sorted((na, nb))))
        for axis, other in ((a, b), (b, a)):
            vr, vc = other[0] - axis[0], other[1] - axis[1]
            for rr, rc in ((-vc, vr), (vc, -vr)):
                new, diag = (axis[0] + rr, axis[1] + rc), (other[0] + rr, other[1] + rc)
                if free(new) and free(diag):
                    cand.append(tuple(sorted((axis, new))))
        for t in cand:
            if t not in par:
                par[t] = s
                q.append(t)


if __name__ == "__main__":
    ex = [[0, 0, 0, 1, 1], [0, 0, 0, 1, 0], [0, 1, 0, 1, 1], [1, 1, 0, 0, 1], [0, 0, 0, 0, 0]]
    assert solution(ex) == 7 == by_vectors(ex)
    p = path_of(ex)
    assert p == [((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (1, 2)), ((1, 2), (2, 2)),
                 ((2, 2), (3, 2)), ((3, 2), (4, 2)), ((4, 2), (4, 3)), ((4, 3), (4, 4))]
    # 무작위 비교(도착할 수 있는 판만)
    rng = random.Random(60063)
    tested = 0
    while tested < 800:
        N = rng.randint(5, 7)
        b = [[1 if rng.random() < 0.2 else 0 for _ in range(N)] for _ in range(N)]
        b[0][0] = b[0][1] = 0
        b[N - 1][N - 1] = 0
        want = by_vectors(b)
        if want == -1:
            continue
        assert solution(b) == want, b
        tested += 1
    # 가장 큰 판(100×100, 빈 판)
    big = [[0] * 100 for _ in range(100)]
    assert solution(big) == by_vectors(big)
    print("ALL CHECKS PASSED")
