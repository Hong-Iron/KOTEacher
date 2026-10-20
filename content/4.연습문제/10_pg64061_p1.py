"""크레인 인형뽑기 게임 (프로그래머스 64061) 풀이와 검증."""
import copy
import random


def solution(board, moves):
    basket = []
    popped = 0
    n = len(board)
    for m in moves:
        col = m - 1
        for row in range(n):
            doll = board[row][col]
            if doll != 0:
                board[row][col] = 0
                if basket and basket[-1] == doll:
                    basket.pop()
                    popped += 2
                else:
                    basket.append(doll)
                break
    return popped


def by_column_stacks(board, moves):
    """열마다 인형 스택(맨 위가 끝)을 미리 만든다."""
    n = len(board)
    cols = [[board[r][c] for r in range(n - 1, -1, -1) if board[r][c]] for c in range(n)]
    basket, popped = [], 0
    for m in moves:
        if cols[m - 1]:
            doll = cols[m - 1].pop()
            if basket and basket[-1] == doll:
                basket.pop()
                popped += 2
            else:
                basket.append(doll)
    return popped


def picks(board, moves):
    b = copy.deepcopy(board)
    out = []
    for m in moves:
        for row in range(len(b)):
            if b[row][m - 1]:
                out.append(b[row][m - 1])
                b[row][m - 1] = 0
                break
        else:
            out.append(None)
    return out


if __name__ == "__main__":
    ex = [[0, 0, 0, 0, 0], [0, 0, 1, 0, 3], [0, 2, 5, 0, 1], [4, 2, 4, 4, 2], [3, 5, 1, 3, 1]]
    mv = [1, 5, 3, 5, 1, 2, 1, 4]
    assert picks(ex, mv) == [4, 3, 1, 1, 3, 2, None, 4]      # 6단계 표
    assert solution(copy.deepcopy(ex), mv) == 4
    assert solution([[0, 0, 0], [0, 1, 0], [2, 1, 3]], [2, 2, 1, 3]) == 2
    rng = random.Random(64061)
    for _ in range(2000):
        n = rng.randint(1, 6)
        board = [[0] * n for _ in range(n)]
        for c in range(n):
            h = rng.randint(0, n)
            for r in range(n - h, n):
                board[r][c] = rng.randint(1, 3)
        moves = [rng.randint(1, n) for _ in range(rng.randint(1, 15))]
        assert solution(copy.deepcopy(board), moves) == by_column_stacks(board, moves)
    print("ALL CHECKS PASSED")
