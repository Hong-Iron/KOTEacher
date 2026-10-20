"""프렌즈4블록 (프로그래머스 17679) 풀이와 검증."""
import random


def solution(m, n, board, trace=None):
    b = [list(row) for row in board]
    total = 0
    while True:
        hit = set()
        for r in range(m - 1):
            for c in range(n - 1):
                x = b[r][c]
                if x != "." and x == b[r][c + 1] == b[r + 1][c] == b[r + 1][c + 1]:
                    hit |= {(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)}
        if not hit:
            return total
        if trace is not None:
            trace.append(len(hit))
        total += len(hit)
        for r, c in hit:
            b[r][c] = "."
        for c in range(n):
            blocks = [b[r][c] for r in range(m) if b[r][c] != "."]
            for r in range(m):
                b[r][c] = "."
            for i, x in enumerate(reversed(blocks)):
                b[m - 1 - i][c] = x


def by_columns(m, n, board):
    """열마다 문자열(아래→위)로 들고 다닌다. 지울 칸은 표시 판으로."""
    cols = ["".join(board[r][c] for r in range(m - 1, -1, -1)) for c in range(n)]  # cols[c][h]: 바닥에서 h번째
    removed = 0
    while True:
        mark = [[False] * m for _ in range(n)]
        found = False
        for c in range(n - 1):
            for h in range(m - 1):
                if h + 1 < len(cols[c]) and h + 1 < len(cols[c + 1]):
                    x = cols[c][h]
                    if x == cols[c][h + 1] == cols[c + 1][h] == cols[c + 1][h + 1]:
                        for cc, hh in ((c, h), (c, h + 1), (c + 1, h), (c + 1, h + 1)):
                            mark[cc][hh] = True
                        found = True
        if not found:
            return removed
        for c in range(n):
            keep = "".join(ch for h, ch in enumerate(cols[c]) if not mark[c][h])
            removed += len(cols[c]) - len(keep)
            cols[c] = keep


if __name__ == "__main__":
    tr = []
    assert solution(4, 5, ["CCBDE", "AAADE", "AAABF", "CCBBF"], tr) == 14 and tr == [6, 8]
    assert solution(6, 6, ["TTTANT", "RRFACC", "RRRFCC", "TRRRAA", "TTMMMF", "TMMTTJ"]) == 15
    assert solution(3, 3, ["AAB", "AAB", "CCB"]) == 4
    assert by_columns(4, 5, ["CCBDE", "AAADE", "AAABF", "CCBBF"]) == 14
    rng = random.Random(17679)
    for _ in range(2000):
        m, n = rng.randint(2, 7), rng.randint(2, 7)
        board = ["".join(rng.choice("AB" if rng.random() < 0.7 else "ABC") for _ in range(n)) for _ in range(m)]
        assert solution(m, n, board) == by_columns(m, n, board), board
    print("ALL CHECKS PASSED")
