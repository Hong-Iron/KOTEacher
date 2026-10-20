"""기둥과 보 설치 (프로그래머스 60061) 풀이와 검증."""
import random


def solution(n, build_frame):
    S = set()

    def ok(x, y, a):
        if a == 0:
            return y == 0 or (x, y - 1, 0) in S or (x - 1, y, 1) in S or (x, y, 1) in S
        return (x, y - 1, 0) in S or (x + 1, y - 1, 0) in S or \
            ((x - 1, y, 1) in S and (x + 1, y, 1) in S)

    for x, y, a, b in build_frame:
        if b == 1:
            S.add((x, y, a))
            if not ok(x, y, a):
                S.remove((x, y, a))
        else:
            S.remove((x, y, a))
            if not all(ok(*s) for s in S):
                S.add((x, y, a))
    return [list(s) for s in sorted(S)]


def by_grid(n, build_frame):
    P = [[False] * (n + 2) for _ in range(n + 2)]     # P[x][y]: 기둥
    B = [[False] * (n + 2) for _ in range(n + 2)]     # B[x][y]: 보

    def g(T, x, y):
        return 0 <= x <= n and 0 <= y <= n and T[x][y]

    def valid():
        for x in range(n + 1):
            for y in range(n + 1):
                if P[x][y] and not (y == 0 or g(P, x, y - 1) or g(B, x - 1, y) or g(B, x, y)):
                    return False
                if B[x][y] and not (g(P, x, y - 1) or g(P, x + 1, y - 1) or (g(B, x - 1, y) and g(B, x + 1, y))):
                    return False
        return True

    for x, y, a, b in build_frame:
        T = P if a == 0 else B
        T[x][y] = bool(b)
        if not valid():
            T[x][y] = not bool(b)
    out = []
    for x in range(n + 1):
        for y in range(n + 1):
            if P[x][y]:
                out.append([x, y, 0])
            if B[x][y]:
                out.append([x, y, 1])
    return out


if __name__ == "__main__":
    assert solution(5, [[1, 0, 0, 1], [1, 1, 1, 1], [2, 1, 0, 1], [2, 2, 1, 1], [5, 0, 0, 1], [5, 1, 0, 1],
                        [4, 2, 1, 1], [3, 2, 1, 1]]) == \
        [[1, 0, 0], [1, 1, 1], [2, 1, 0], [2, 2, 1], [3, 2, 1], [4, 2, 1], [5, 0, 0], [5, 1, 0]]
    assert solution(5, [[0, 0, 0, 1], [2, 0, 0, 1], [4, 0, 0, 1], [0, 1, 1, 1], [1, 1, 1, 1], [2, 1, 1, 1],
                        [3, 1, 1, 1], [2, 0, 0, 0], [1, 1, 1, 0], [2, 2, 0, 1]]) == \
        [[0, 0, 0], [0, 1, 1], [1, 1, 1], [2, 1, 1], [3, 1, 1], [4, 0, 0]]
    rng = random.Random(60061)
    for _ in range(2000):
        n = rng.randint(3, 5)
        frames, cur = [], set()
        for _ in range(rng.randint(1, 25)):
            if cur and rng.random() < 0.3:
                x, y, a = rng.choice(sorted(cur))
                frames.append([x, y, a, 0])
                # 실제로 지워질지는 모르니 cur은 풀이로 다시 계산한다
            else:
                a = rng.randint(0, 1)
                x = rng.randint(0, n - 1 if a == 1 else n)
                y = rng.randint(1 if a == 1 else 0, n - 1)
                if (x, y, a) in cur:
                    continue
                frames.append([x, y, a, 1])
            cur = {tuple(s) for s in solution(n, frames)}
        assert solution(n, frames) == by_grid(n, frames), frames
    print("ALL CHECKS PASSED")
