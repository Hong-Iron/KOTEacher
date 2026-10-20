"""키패드 누르기 (프로그래머스 67256) 풀이와 검증."""
import random
from collections import deque


def solution(numbers, hand):
    pos = {1: (0, 0), 2: (0, 1), 3: (0, 2),
           4: (1, 0), 5: (1, 1), 6: (1, 2),
           7: (2, 0), 8: (2, 1), 9: (2, 2),
           "*": (3, 0), 0: (3, 1), "#": (3, 2)}
    left, right = pos["*"], pos["#"]
    answer = ""
    for d in numbers:
        if d in (1, 4, 7):
            use = "L"
        elif d in (3, 6, 9):
            use = "R"
        else:
            r, c = pos[d]
            dl = abs(left[0] - r) + abs(left[1] - c)
            dr = abs(right[0] - r) + abs(right[1] - c)
            if dl < dr:
                use = "L"
            elif dr < dl:
                use = "R"
            else:
                use = "L" if hand == "left" else "R"
        if use == "L":
            left = pos[d]
        else:
            right = pos[d]
        answer += use
    return answer


PAD = ["123", "456", "789", "*0#"]


def bfs_dist(a, b):
    """키패드 칸을 상하좌우로 건너가는 최소 칸 수 (맨해튼 공식을 쓰지 않는다)."""
    where = {PAD[r][c]: (r, c) for r in range(4) for c in range(3)}
    start, goal = where[a], where[b]
    q, seen = deque([(start, 0)]), {start}
    while q:
        (r, c), d = q.popleft()
        if (r, c) == goal:
            return d
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < 4 and 0 <= nc < 3 and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append(((nr, nc), d + 1))


def other(numbers, hand):
    L, R, out = "*", "#", []
    for d in numbers:
        k = str(d)
        if k in "147":
            use = "L"
        elif k in "369":
            use = "R"
        else:
            dl, dr = bfs_dist(L, k), bfs_dist(R, k)
            use = "L" if dl < dr or (dl == dr and hand == "left") else "R"
        if use == "L":
            L = k
        else:
            R = k
        out.append(use)
    return "".join(out)


if __name__ == "__main__":
    assert solution([1, 3, 4, 5, 8, 2, 1, 4, 5, 9, 5], "right") == "LRLLLRLLRRL"
    assert solution([7, 0, 8, 2, 8, 3, 1, 5, 7, 6, 2], "left") == "LRLLRRLLLRR"
    assert solution([1, 2, 3, 4, 5, 6, 7, 8, 9, 0], "right") == "LLRLLRLLRL"
    assert solution([1, 5], "right") == "LL"
    rng = random.Random(67256)
    for _ in range(2000):
        nums = [rng.randint(0, 9) for _ in range(rng.randint(1, 30))]
        h = rng.choice(["left", "right"])
        assert solution(nums, h) == other(nums, h)
    print("ALL CHECKS PASSED")
