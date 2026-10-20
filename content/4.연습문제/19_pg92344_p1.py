"""파괴되지 않은 건물 (프로그래머스 92344) 풀이와 검증."""
import random
import time
from itertools import accumulate


def solution(board, skill):
    N, M = len(board), len(board[0])
    D = [[0] * (M + 1) for _ in range(N + 1)]
    for t, r1, c1, r2, c2, deg in skill:
        v = -deg if t == 1 else deg
        D[r1][c1] += v
        D[r1][c2 + 1] -= v
        D[r2 + 1][c1] -= v
        D[r2 + 1][c2 + 1] += v
    D = [list(accumulate(row)) for row in D]              # 가로로 누적
    for i in range(1, N + 1):                             # 세로로 누적
        up, row = D[i - 1], D[i]
        for j in range(M + 1):
            row[j] += up[j]
    return sum(1 for i in range(N) for j in range(M) if board[i][j] + D[i][j] > 0)


def marks_and_change(N, M, skill):
    D = [[0] * (M + 1) for _ in range(N + 1)]
    for t, r1, c1, r2, c2, deg in skill:
        v = -deg if t == 1 else deg
        D[r1][c1] += v
        D[r1][c2 + 1] -= v
        D[r2 + 1][c1] -= v
        D[r2 + 1][c2 + 1] += v
    marks = [row[:] for row in D]
    rows = [list(accumulate(row)) for row in D]
    cols = [row[:] for row in rows]
    for i in range(1, N + 1):
        for j in range(M + 1):
            cols[i][j] += cols[i - 1][j]
    return marks, rows, cols


def by_cells(board, skill):
    b = [row[:] for row in board]
    for t, r1, c1, r2, c2, deg in skill:
        v = -deg if t == 1 else deg
        for i in range(r1, r2 + 1):
            for j in range(c1, c2 + 1):
                b[i][j] += v
    return sum(1 for row in b for x in row if x > 0)


if __name__ == "__main__":
    assert solution([[5] * 5 for _ in range(4)],
                    [[1, 0, 0, 3, 4, 4], [1, 2, 0, 2, 3, 2], [2, 1, 0, 3, 1, 2], [1, 0, 1, 3, 3, 1]]) == 10
    ex2 = ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[1, 1, 1, 2, 2, 4], [1, 0, 0, 1, 1, 2], [2, 2, 0, 2, 0, 100]])
    assert solution(*ex2) == 6
    # 6단계 추적: 예시 2의 표시판과 누적 결과
    marks, rows, cols = marks_and_change(3, 3, ex2[1])
    assert marks == [[-2, 0, 2, 0], [0, -4, 0, 4], [102, -100, -2, 0], [-100, 104, 0, -4]], marks
    assert [r[:3] for r in rows[:3]] == [[-2, -2, 0], [0, -4, -4], [102, 2, 0]], rows
    assert [r[:3] for r in cols[:3]] == [[-2, -2, 0], [-2, -6, -4], [100, -4, -4]], cols
    final = [[ex2[0][i][j] + cols[i][j] for j in range(3)] for i in range(3)]
    assert final == [[-1, 0, 3], [2, -1, 2], [107, 4, 5]], final
    # 네 번째 모서리를 빠뜨리면 오른쪽 아래 바깥(i > r2, j > c2)이 모두 -v만큼 틀어진다
    D = [[0] * 5 for _ in range(5)]
    v = 3
    D[1][1] += v; D[1][3] -= v; D[3][1] -= v                  # (3, 3)의 +v를 빠뜨림
    D = [list(accumulate(r)) for r in D]
    D = [list(c) for c in zip(*[list(accumulate(col)) for col in zip(*D)])]
    want = [[v if 1 <= i <= 2 and 1 <= j <= 2 else 0 for j in range(5)] for i in range(5)]
    assert all(D[i][j] - want[i][j] == (-v if i >= 3 and j >= 3 else 0) for i in range(5) for j in range(5))
    assert accumulate([3, 1, 2]) and list(accumulate([3, 1, 2])) == [3, 4, 6]
    # 무작위 비교
    rng = random.Random(92344)
    for _ in range(2000):
        N, M = rng.randint(1, 6), rng.randint(1, 6)
        board = [[rng.randint(1, 9) for _ in range(M)] for _ in range(N)]
        skill = []
        for _ in range(rng.randint(1, 8)):
            r1 = rng.randrange(N); r2 = rng.randrange(r1, N); c1 = rng.randrange(M); c2 = rng.randrange(c1, M)
            skill.append([rng.randint(1, 2), r1, c1, r2, c2, rng.randint(1, 9)])
        assert solution(board, skill) == by_cells(board, skill), (board, skill)
    # 효율성: 1000 × 1000, 스킬 25만 개
    board = [[rng.randint(1, 1000) for _ in range(1000)] for _ in range(1000)]
    skill = []
    for _ in range(250_000):
        r1 = rng.randrange(1000); r2 = rng.randrange(r1, 1000); c1 = rng.randrange(1000); c2 = rng.randrange(c1, 1000)
        skill.append([rng.randint(1, 2), r1, c1, r2, c2, rng.randint(1, 500)])
    t0 = time.perf_counter()
    solution(board, skill)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"1000x1000, 250k skills: {t:.2f}s")
    print("ALL CHECKS PASSED")
