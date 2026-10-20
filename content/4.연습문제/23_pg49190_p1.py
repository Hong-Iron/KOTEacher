"""방의 개수 (프로그래머스 49190) 풀이와 검증."""
import random
import time
from collections import deque

MOVES = ((0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1))   # 0 위, 시계 방향


def solution(arrows, halves=2):
    x, y = 0, 0
    points = {(0, 0)}
    edges = set()
    rooms = 0
    for d in arrows:
        dx, dy = MOVES[d]
        for _ in range(halves):                # 한 칸을 반 칸씩 두 번 간다
            nx, ny = x + dx, y + dy
            e = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
            if e not in edges:
                if (nx, ny) in points:
                    rooms += 1                 # 새 선이 이미 있던 점에 닿으면 방이 하나 닫힌다
                edges.add(e)
                points.add((nx, ny))
            x, y = nx, ny
    return rooms


def mistake(arrows, mode):
    """흔한 실수 확인용. mode="points": 선을 안 보고 점만 본다. mode="directed": 선에 방향을 둔다."""
    x, y = 0, 0
    points, edges, rooms = {(0, 0)}, set(), 0
    for d in arrows:
        dx, dy = MOVES[d]
        for _ in range(2):
            nx, ny = x + dx, y + dy
            e = ((x, y), (nx, ny))
            if mode == "points" or e not in edges:
                if (nx, ny) in points:
                    rooms += 1
                edges.add(e)
                points.add((nx, ny))
            x, y = nx, ny
    return rooms


def by_pixels(arrows, scale=6):
    """선을 점으로 찍어 그리고, 선이 아닌 칸의 덩어리 수를 센다(작은 입력만)."""
    x, y = 0, 0
    ink = {(0, 0)}
    for d in arrows:
        dx, dy = MOVES[d]
        for _ in range(scale):
            x, y = x + dx, y + dy
            ink.add((x, y))
    xs = [p[0] for p in ink]
    ys = [p[1] for p in ink]
    x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys) - 1, max(ys) + 1
    seen = set(ink)
    parts = 0
    for sx in range(x0, x1 + 1):
        for sy in range(y0, y1 + 1):
            if (sx, sy) in seen:
                continue
            parts += 1
            seen.add((sx, sy))
            q = deque([(sx, sy)])
            while q:
                cx, cy = q.popleft()
                for ax, ay in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if x0 <= ax <= x1 and y0 <= ay <= y1 and (ax, ay) not in seen:
                        seen.add((ax, ay))
                        q.append((ax, ay))
    return parts - 1                           # 바깥 하나를 뺀다


if __name__ == "__main__":
    ex = [6, 6, 6, 4, 4, 4, 2, 2, 2, 0, 0, 0, 1, 6, 5, 5, 3, 6, 0]
    assert solution(ex) == 3 == by_pixels(ex)
    # 1단계·3단계의 예
    assert solution([2, 0, 6, 4]) == 1                     # 정사각형 한 바퀴
    assert solution([2, 0, 6, 4, 2, 0]) == 1               # 같은 선을 다시 그어도 그대로
    assert solution([1, 4, 7]) == 1 == by_pixels([1, 4, 7])   # 대각선 두 개가 엇갈린다
    assert solution([1, 4, 7], halves=1) == 0              # 반 칸으로 나누지 않으면 놓친다
    assert mistake([2, 0, 6, 4, 2, 0], "points") == 5 and mistake([2, 6], "directed") == 2 and solution([2, 6]) == 0
    assert solution([2, 0, 6, 4, 1, 6, 3]) == 4 == by_pixels([2, 0, 6, 4, 1, 6, 3])   # X자 정사각형
    rng = random.Random(49190)
    for _ in range(1500):
        arrows = [rng.randrange(8) for _ in range(rng.randint(1, 30))]
        assert solution(arrows) == by_pixels(arrows), arrows
    # 좁은 곳을 맴돌아 선이 많이 겹치는 경우
    for _ in range(500):
        arrows, x, y = [], 0, 0
        for _ in range(rng.randint(1, 40)):
            d = rng.randrange(8)
            dx, dy = MOVES[d]
            if abs(x + dx) <= 2 and abs(y + dy) <= 2:
                arrows.append(d)
                x, y = x + dx, y + dy
        assert solution(arrows) == by_pixels(arrows), arrows
    big = [rng.randrange(8) for _ in range(100_000)]
    t0 = time.perf_counter()
    solution(big)
    solution([0, 2, 4, 6] * 25_000)
    t = time.perf_counter() - t0
    assert solution([0, 2, 4, 6] * 25_000) == 1
    assert t < 5, t
    print(f"화살표 10만 개 두 번: {t:.2f}s")
    print("ALL CHECKS PASSED")
