"""블록 게임 (프로그래머스 42894) 풀이와 검증."""
import random
from collections import defaultdict


def solution(board, log=None):
    N = len(board)
    b = [row[:] for row in board]

    def can_drop(r, c):                        # 위에서 검은 블록을 (r, c)까지 떨어뜨릴 수 있나
        return all(b[i][c] == 0 for i in range(r + 1))

    removed = 0
    while True:
        cells = defaultdict(list)
        for r in range(N):
            for c in range(N):
                if b[r][c]:
                    cells[b[r][c]].append((r, c))
        done = False
        for bid, cs in cells.items():
            r1, r2 = min(r for r, _ in cs), max(r for r, _ in cs)
            c1, c2 = min(c for _, c in cs), max(c for _, c in cs)
            if (r2 - r1 + 1) * (c2 - c1 + 1) != 6:
                continue                        # 2×3 또는 3×2 상자가 아니면 직사각형이 될 수 없다
            holes = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1) if b[r][c] != bid]
            if all(b[r][c] == 0 and can_drop(r, c) for r, c in holes):
                for r, c in cs:
                    b[r][c] = 0
                removed += 1
                if log is not None:
                    log.append((bid, holes))
                done = True
                break                           # 판이 바뀌었으니 처음부터 다시 본다
        if not done:
            return removed


def by_black_fill(board):
    """열마다 위에서부터 닿는 빈칸을 모두 검은 블록(-1)으로 채우고, 채워진 직사각형을 지우기를 되풀이한다."""
    N = len(board)
    b = [row[:] for row in board]
    removed = 0
    while True:
        for c in range(N):
            for r in range(N):
                if b[r][c] > 0:
                    break
                b[r][c] = -1
        blocks = defaultdict(list)
        for r in range(N):
            for c in range(N):
                if b[r][c] > 0:
                    blocks[b[r][c]].append((r, c))
        gone = []
        for bid, cs in blocks.items():
            r1, r2 = min(r for r, _ in cs), max(r for r, _ in cs)
            c1, c2 = min(c for _, c in cs), max(c for _, c in cs)
            box = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
            if len(box) == 6 and all(b[r][c] in (bid, -1) for r, c in box):
                gone.append(bid)
        if not gone:
            return removed
        for bid in gone:
            for r, c in blocks[bid]:
                b[r][c] = 0
            removed += 1


SHAPES = []
for base in ([(0, 0), (1, 0), (1, 1), (1, 2)],      # ㄴ 모양
             [(0, 2), (1, 0), (1, 1), (1, 2)],      # 거꾸로 ㄴ
             [(0, 1), (1, 0), (1, 1), (1, 2)]):     # ㅗ 모양
    cur = base
    for _ in range(4):
        mr, mc = min(r for r, _ in cur), min(c for _, c in cur)
        norm = tuple(sorted((r - mr, c - mc) for r, c in cur))
        if norm not in SHAPES:
            SHAPES.append(norm)
        cur = [(c, -r) for r, c in cur]


def random_board(rng, N, tries):
    b = [[0] * N for _ in range(N)]
    bid = 1
    for _ in range(tries):
        sh = rng.choice(SHAPES)
        r0, c0 = rng.randrange(N), rng.randrange(N)
        cells = [(r0 + r, c0 + c) for r, c in sh]
        if all(0 <= r < N and 0 <= c < N and b[r][c] == 0 for r, c in cells):
            for r, c in cells:
                b[r][c] = bid
            bid += 1
    return b


if __name__ == "__main__":
    assert len(SHAPES) == 12
    ex = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 4, 0, 0, 0], [0, 0, 0, 0, 0, 4, 4, 0, 0, 0],
          [0, 0, 0, 0, 3, 0, 4, 0, 0, 0], [0, 0, 0, 2, 3, 0, 0, 0, 5, 5], [1, 2, 2, 2, 3, 3, 0, 0, 0, 5],
          [1, 1, 1, 0, 0, 0, 0, 0, 0, 5]]
    assert solution(ex) == 2 == by_black_fill(ex)
    lg = []
    solution(ex, lg)
    assert lg == [(2, [(7, 1), (7, 2)]), (1, [(8, 1), (8, 2)])]
    rng = random.Random(42894)
    for _ in range(1500):
        N = rng.randint(4, 8)
        bd = random_board(rng, N, rng.randint(1, 12))
        assert solution(bd) == by_black_fill(bd), bd
    big = random_board(rng, 50, 800)
    assert solution(big) == by_black_fill(big)
    print("ALL CHECKS PASSED")
