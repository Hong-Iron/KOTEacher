"""행렬과 연산 (프로그래머스 118670) 풀이와 검증."""
import random
import time
from collections import deque


def solution(rc, operations):
    left = deque(row[0] for row in rc)                 # 첫 열
    right = deque(row[-1] for row in rc)               # 끝 열
    mid = deque(deque(row[1:-1]) for row in rc)        # 가운데 부분(행마다)
    for op in operations:
        if op == "ShiftRow":                           # 모든 행을 아래로 한 칸
            left.appendleft(left.pop())
            right.appendleft(right.pop())
            mid.appendleft(mid.pop())
        else:                                          # 바깥 테두리를 시계 방향으로 한 칸
            mid[0].appendleft(left.popleft())          # 왼쪽 위 → 첫 행 가운데 맨 앞
            right.appendleft(mid[0].pop())             # 첫 행 가운데 맨 뒤 → 오른쪽 열 맨 위
            mid[-1].append(right.pop())                # 오른쪽 열 맨 아래 → 끝 행 가운데 맨 뒤
            left.append(mid[-1].popleft())             # 끝 행 가운데 맨 앞 → 왼쪽 열 맨 아래
    return [[left[i]] + list(mid[i]) + [right[i]] for i in range(len(rc))]


def by_matrix(rc, operations):
    a = [row[:] for row in rc]
    R, C = len(a), len(a[0])
    for op in operations:
        if op == "ShiftRow":
            a = [a[-1]] + a[:-1]
        else:
            ring = [(0, c) for c in range(C)] + [(r, C - 1) for r in range(1, R)] + \
                   [(R - 1, c) for c in range(C - 2, -1, -1)] + [(r, 0) for r in range(R - 2, 0, -1)]
            vals = [a[r][c] for r, c in ring]
            vals = [vals[-1]] + vals[:-1]
            for (r, c), v in zip(ring, vals):
                a[r][c] = v
    return a


if __name__ == "__main__":
    exs = [
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], ["Rotate", "ShiftRow"], [[8, 9, 6], [4, 1, 2], [7, 5, 3]]),
        ([[8, 6, 3], [3, 3, 7], [8, 4, 9]], ["Rotate", "ShiftRow", "ShiftRow"], [[8, 3, 3], [4, 9, 7], [3, 8, 6]]),
        ([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]], ["ShiftRow", "Rotate", "ShiftRow", "Rotate"],
         [[1, 6, 7, 8], [5, 9, 10, 4], [2, 3, 12, 11]]),
    ]
    for rc, ops, want in exs:
        assert solution(rc, ops) == want == by_matrix(rc, ops)
    # 6단계 추적: 3×3에 Rotate 한 번
    assert solution([[1, 2, 3], [4, 5, 6], [7, 8, 9]], ["Rotate"]) == [[4, 1, 2], [7, 5, 3], [8, 9, 6]]
    L, Rt, M = deque([1, 4, 7]), deque([3, 6, 9]), deque([deque([2]), deque([5]), deque([8])])
    snaps = []
    M[0].appendleft(L.popleft()); snaps.append((list(L), list(Rt), list(M[0]), list(M[-1])))
    Rt.appendleft(M[0].pop()); snaps.append((list(L), list(Rt), list(M[0]), list(M[-1])))
    M[-1].append(Rt.pop()); snaps.append((list(L), list(Rt), list(M[0]), list(M[-1])))
    L.append(M[-1].popleft()); snaps.append((list(L), list(Rt), list(M[0]), list(M[-1])))
    assert snaps == [([4, 7], [3, 6, 9], [1, 2], [8]), ([4, 7], [2, 3, 6, 9], [1], [8]),
                     ([4, 7], [2, 3, 6], [1], [8, 9]), ([4, 7, 8], [2, 3, 6], [1], [9])]
    # 열이 2개면 가운데가 비어 있다
    assert solution([[1, 2], [3, 4]], ["Rotate"]) == [[3, 1], [4, 2]] == by_matrix([[1, 2], [3, 4]], ["Rotate"])
    rng = random.Random(118670)
    for _ in range(2000):
        R, C = rng.randint(2, 5), rng.randint(2, 5)
        rc = [[rng.randint(1, 99) for _ in range(C)] for _ in range(R)]
        ops = [rng.choice(["ShiftRow", "Rotate"]) for _ in range(rng.randint(1, 12))]
        assert solution(rc, ops) == by_matrix(rc, ops), (rc, ops)
    # 효율성: 원소 10만 개, 연산 10만 개
    for R, C in ((2, 50_000), (50_000, 2), (316, 316)):
        rc = [[rng.randint(1, 10 ** 6) for _ in range(C)] for _ in range(R)]
        ops = [rng.choice(["ShiftRow", "Rotate"]) for _ in range(100_000)]
        t0 = time.perf_counter()
        solution(rc, ops)
        t = time.perf_counter() - t0
        assert t < 10, t
        print(f"{R}x{C}: {t:.2f}s")
    print("ALL CHECKS PASSED")
