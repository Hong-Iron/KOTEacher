"""직사각형의 넓이 (프로그래머스 12974) 풀이와 검증."""
import random
import time


def solution(rectangles, trace=None):
    ys = sorted({y for _, y1, _, y2 in rectangles for y in (y1, y2)})
    where = {y: i for i, y in enumerate(ys)}
    m = len(ys) - 1                            # 칸: ys[i] ~ ys[i + 1]
    size = 1
    while size < m:
        size *= 2
    length = [0] * (2 * size)                  # 마디가 맡은 y 길이
    for i in range(m):
        length[size + i] = ys[i + 1] - ys[i]
    for i in range(size - 1, 0, -1):
        length[i] = length[2 * i] + length[2 * i + 1]
    cnt = [0] * (2 * size)                     # 마디 전체를 통째로 덮는 직사각형 수
    cov = [0] * (2 * size)                     # 마디 안에서 덮인 길이

    def pull(i):
        if cnt[i] > 0:
            cov[i] = length[i]
        elif i >= size:
            cov[i] = 0
        else:
            cov[i] = cov[2 * i] + cov[2 * i + 1]

    def update(l, r, v):                       # 칸 l ~ r − 1에 v를 더한다
        l += size
        r += size
        l0, r0 = l, r - 1
        while l < r:
            if l & 1:
                cnt[l] += v
                pull(l)
                l += 1
            if r & 1:
                r -= 1
                cnt[r] += v
                pull(r)
            l >>= 1
            r >>= 1
        for i in (l0, r0):                     # 바뀐 마디의 조상을 다시 계산한다
            i >>= 1
            while i:
                pull(i)
                i >>= 1

    events = []
    for x1, y1, x2, y2 in rectangles:
        events.append((x1, 1, where[y1], where[y2]))   # 들어온다
        events.append((x2, -1, where[y1], where[y2]))  # 나간다
    events.sort()
    area = 0
    prev_x = events[0][0]
    for x, v, lo, hi in events:
        area += cov[1] * (x - prev_x)          # 직전 x부터 지금 x까지 덮인 길이 × 폭
        if trace is not None and x != prev_x:
            trace.append((prev_x, x, cov[1]))
        update(lo, hi, v)
        prev_x = x
    return area


def by_cells(rectangles):
    """좌표를 압축한 칸마다 덮였는지 본다(작은 입력만)."""
    xs = sorted({x for x1, _, x2, _ in rectangles for x in (x1, x2)})
    ys = sorted({y for _, y1, _, y2 in rectangles for y in (y1, y2)})
    area = 0
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx, cy = xs[i], ys[j]
            if any(x1 <= cx < x2 and y1 <= cy < y2 for x1, y1, x2, y2 in rectangles):
                area += (xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j])
    return area


if __name__ == "__main__":
    assert solution([[0, 1, 4, 4], [3, 1, 5, 3]]) == 14
    ex2 = [[1, 1, 6, 5], [2, 0, 4, 2], [2, 4, 5, 7], [4, 3, 8, 6], [7, 5, 9, 7]]
    assert solution(ex2) == 38 == by_cells(ex2)
    # 6단계 추적: 예시 1
    tr = []
    solution([[0, 1, 4, 4], [3, 1, 5, 3]], tr)
    assert tr == [(0, 3, 3), (3, 4, 3), (4, 5, 2)]
    rng = random.Random(12974)
    for _ in range(2000):
        n = rng.randint(1, 8)
        span = rng.choice([5, 20, 10 ** 9])
        rects = []
        for _ in range(n):
            x1, x2 = sorted(rng.sample(range(span + 1), 2))
            y1, y2 = sorted(rng.sample(range(span + 1), 2))
            rects.append([x1, y1, x2, y2])
        assert solution(rects) == by_cells(rects), rects
    # 직사각형 10만 개
    big = []
    for _ in range(100_000):
        x1, x2 = sorted(rng.sample(range(10 ** 9 + 1), 2))
        y1, y2 = sorted(rng.sample(range(10 ** 9 + 1), 2))
        big.append([x1, y1, x2, y2])
    thin = [[i, i, i + 2, 10 ** 9 - i] for i in range(100_000)]   # 서로 많이 겹치는 경우
    t0 = time.perf_counter()
    solution(big)
    solution(thin)
    t = time.perf_counter() - t0
    assert solution(thin[:300]) == by_cells(thin[:300])
    assert t < 30, t
    print(f"직사각형 10만 개 두 번: {t:.1f}s")
    print("ALL CHECKS PASSED")
