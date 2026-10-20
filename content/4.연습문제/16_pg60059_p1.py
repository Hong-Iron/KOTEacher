"""자물쇠와 열쇠 (프로그래머스 60059) 풀이와 검증."""
import random


def solution(key, lock):
    N, M = len(lock), len(key)
    if all(v == 1 for row in lock for v in row):
        return True

    def fits(k, dr, dc):
        for r in range(N):
            for c in range(N):
                kr, kc = r - dr, c - dc
                kv = k[kr][kc] if 0 <= kr < M and 0 <= kc < M else 0
                if lock[r][c] + kv != 1:
                    return False
        return True

    for _ in range(4):
        key = [list(r) for r in zip(*key[::-1])]
        for dr in range(-(M - 1), N):
            for dc in range(-(M - 1), N):
                if fits(key, dr, dc):
                    return True
    return False


def by_sets(key, lock):
    """열쇠 돌기 좌표 집합을 돌리고 옮겨, 자물쇠 홈 집합과 정확히 같은지 본다(자물쇠 안에서)."""
    N, M = len(lock), len(key)
    holes = {(r, c) for r in range(N) for c in range(N) if lock[r][c] == 0}
    if not holes:
        return True
    bumps = {(r, c) for r in range(M) for c in range(M) if key[r][c] == 1}
    for _ in range(4):
        bumps = {(c, M - 1 - r) for r, c in bumps}          # 시계 방향 90도
        for dr in range(-M, N + 1):
            for dc in range(-M, N + 1):
                inside = {(r + dr, c + dc) for r, c in bumps if 0 <= r + dr < N and 0 <= c + dc < N}
                if inside == holes:
                    return True
    return False


if __name__ == "__main__":
    key = [[0, 0, 0], [1, 0, 0], [0, 1, 1]]
    lock = [[1, 1, 1], [1, 1, 0], [1, 0, 1]]
    assert solution(key, lock) is True
    rot1 = [list(r) for r in zip(*key[::-1])]
    assert rot1 == [[0, 1, 0], [1, 0, 0], [1, 0, 0]]
    rng = random.Random(60059)
    for _ in range(1500):
        M = rng.randint(3, 4)
        N = rng.randint(M, 5)
        k = [[rng.randint(0, 1) for _ in range(M)] for _ in range(M)]
        lk = [[1 if rng.random() < 0.8 else 0 for _ in range(N)] for _ in range(N)]
        assert solution(k, lk) == by_sets(k, lk), (k, lk)
    print("ALL CHECKS PASSED")
