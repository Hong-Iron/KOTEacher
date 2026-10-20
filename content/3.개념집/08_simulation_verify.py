"""08.구현과 시뮬레이션 문서의 주장을 확인한다."""
import random

DR = [-1, 1, 0, 0]
DC = [0, 0, -1, 1]


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def neighbors(r, c, n):
    out = []
    for d in range(4):
        nr, nc = r + DR[d], c + DC[d]
        if 0 <= nr < n and 0 <= nc < n:
            out.append((nr, nc))
    return out


def main():
    # 예시 표
    move = {"위": (-1, 0), "아래": (1, 0), "왼쪽": (0, -1), "오른쪽": (0, 1)}
    r, c, n = 1, 1, 3
    trail = []
    for cmd in ["위", "위", "오른쪽"]:
        nr, nc = r + move[cmd][0], c + move[cmd][1]
        if 0 <= nr < n and 0 <= nc < n:
            r, c = nr, nc
        trail.append((r, c))
    check(trail == [(0, 1), (0, 1), (0, 2)], "예시 표")
    check(neighbors(1, 1, 3) == [(0, 1), (2, 1), (1, 0), (1, 2)], "이웃 네 칸")
    check(neighbors(0, 3, 4) == [(1, 3), (0, 2)], "C1")
    grid = [[1, 2], [3, 4]]
    check(grid[-1] == [3, 4], "음수 번호는 오류 없이 끝 줄")
    # 회전
    a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    check([list(x) for x in zip(*a[::-1])] == [[7, 4, 1], [8, 5, 2], [9, 6, 3]], "90도 회전")
    check([list(x) for x in zip(*a)] == [[1, 4, 7], [2, 5, 8], [3, 6, 9]], "전치")
    rng = random.Random(8)
    for _ in range(500):
        n = rng.randint(1, 6)
        m = [[rng.randint(0, 9) for _ in range(n)] for _ in range(n)]
        rot = [list(x) for x in zip(*m[::-1])]
        for rr in range(n):
            for cc in range(n):
                check(rot[cc][n - 1 - rr] == m[rr][cc], "회전 공식")
    b = [[1, 2, 3], [4, 5, 6]]
    check([list(x) for x in zip(*b[::-1])] == [[4, 1], [5, 2], [6, 3]], "C3")
    check(abs(0 - 2) + abs(1 - 0) == 3, "맨해튼 거리")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
