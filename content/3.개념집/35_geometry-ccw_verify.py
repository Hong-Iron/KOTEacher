"""계산 기하 기초: 문서의 예시 값, 확인 문제 답, 무작위 비교."""
import math
import random
from fractions import Fraction
from functools import cmp_to_key


def cross(o, p, q):
    return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])


def ccw(o, p, q):
    c = cross(o, p, q)
    return (c > 0) - (c < 0)                   # 1: 왼쪽으로 꺾음, −1: 오른쪽, 0: 한 줄


def on_segment(p, q, r):
    return min(p[0], q[0]) <= r[0] <= max(p[0], q[0]) and min(p[1], q[1]) <= r[1] <= max(p[1], q[1])


def segments_meet(p1, p2, q1, q2):
    """두 선분이 한 점이라도 만나는가 (끝점에 닿는 것, 한 줄로 겹치는 것 포함)."""
    d1, d2 = ccw(p1, p2, q1), ccw(p1, p2, q2)
    d3, d4 = ccw(q1, q2, p1), ccw(q1, q2, p2)
    if d1 * d2 < 0 and d3 * d4 < 0:
        return True
    return ((d1 == 0 and on_segment(p1, p2, q1)) or (d2 == 0 and on_segment(p1, p2, q2)) or
            (d3 == 0 and on_segment(q1, q2, p1)) or (d4 == 0 and on_segment(q1, q2, p2)))


def meet_exact(p1, p2, q1, q2):
    """분수로 직접 풀어 본다: p1 + s(p2 − p1) = q1 + t(q2 − q1), 0 ≤ s, t ≤ 1."""
    ax, ay = p2[0] - p1[0], p2[1] - p1[1]
    bx, by = q2[0] - q1[0], q2[1] - q1[1]
    cx, cy = q1[0] - p1[0], q1[1] - p1[1]
    den = ax * by - ay * bx
    if den != 0:
        s = Fraction(cx * by - cy * bx, den)
        t = Fraction(cx * ay - cy * ax, den)
        return 0 <= s <= 1 and 0 <= t <= 1
    if ax * cy - ay * cx != 0:                 # 평행하고 한 줄이 아니다
        return False
    pts = [p1, p2]
    return any(on_segment(q1, q2, p) for p in pts) or any(on_segment(p1, p2, q) for q in (q1, q2))


def in_triangle(a, b, c, p):
    """p가 삼각형 abc 안이나 변 위에 있는가."""
    s = {ccw(a, b, p), ccw(b, c, p), ccw(c, a, p)}
    return not (1 in s and -1 in s)


if __name__ == "__main__":
    O, P, Q = (0, 0), (4, 1), (1, 3)
    assert cross(O, P, Q) == 11 and ccw(O, P, Q) == 1 and ccw(O, Q, P) == -1
    assert abs(cross(O, P, Q)) == 2 * Fraction(11, 2)  # 삼각형 넓이의 두 배
    # 확인 문제 C1
    assert cross((1, 1), (5, 2), (3, -4)) == -22
    # 확인 문제 C3: 한쪽 검사만 하면 만난다고 잘못 본다
    a1, a2, b1, b2 = (0, 0), (2, 0), (5, -1), (5, 1)
    assert ccw(a1, a2, b1) * ccw(a1, a2, b2) < 0 and ccw(b1, b2, a1) * ccw(b1, b2, a2) > 0
    assert not segments_meet(a1, a2, b1, b2)
    # 오해: 기울기로 나누면 세로선에서 0으로 나눈다
    try:
        (3 - 1) / (2 - 2)
        raise RuntimeError
    except ZeroDivisionError:
        pass
    # 부동소수 기울기가 같은 줄을 놓치는 예: 아주 큰 좌표에서 float 비교가 틀린다
    o, p, q = (0, 0), (10 ** 17, 10 ** 17 + 1), (10 ** 17 + 1, 10 ** 17 + 2)
    assert ccw(o, p, q) == -1 and p[1] / p[0] == q[1] / q[0]   # 기울기는 둘 다 1.0으로 보인다
    rng = random.Random(35)
    for _ in range(20000):
        pts = [(rng.randint(-6, 6), rng.randint(-6, 6)) for _ in range(4)]
        if pts[0] == pts[1] or pts[2] == pts[3]:
            continue                           # 길이 0인 선분은 빼고 본다
        assert segments_meet(*pts) == meet_exact(*pts), pts
        a, b, c, p = pts
        if ccw(a, b, c) != 0:
            area = abs(cross(a, b, c))
            parts = abs(cross(p, a, b)) + abs(cross(p, b, c)) + abs(cross(p, c, a))
            assert in_triangle(a, b, c, p) == (parts == area)
    # 각도 순 정렬: 한 점에서 본 순서를 atan2와 비교 (위쪽 반평면 안의 점들)
    for _ in range(500):
        o = (0, 0)
        pts = list({(rng.randint(-50, 50), rng.randint(1, 50)) for _ in range(15)})
        pts = [p for i, p in enumerate(pts) if all(ccw(o, p, q) != 0 for q in pts[:i])]
        by_cross = sorted(pts, key=cmp_to_key(lambda p, q: -ccw(o, p, q)))
        assert by_cross == sorted(pts, key=lambda p: math.atan2(p[1], p[0]))
    print("ALL CHECKS PASSED")
