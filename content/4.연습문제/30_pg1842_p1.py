"""네오의 귀걸이 (프로그래머스 1842) 풀이와 검증."""
import random
import time
from bisect import bisect_left, bisect_right
from collections import defaultdict

MOD = 1_000_000_007


def solution(n, point, query, table=None):
    pts = sorted(tuple(p) for p in point)      # x가 작은 것부터 (x는 모두 다르다)
    s_xy = pts[0][:2]                          # S: 가장 왼쪽 점
    e_xy = pts[-1][:2]                         # E: 가장 오른쪽 점

    # f: S에서 이 점까지 오는 사슬 수. u = x − y가 같은 점끼리 x 순서로 모은다
    gx = defaultdict(list)                     # u → x들
    gf = defaultdict(lambda: [0])              # u → f의 누적 합
    f = {}
    for x, y, k in pts:
        v = 1 if (x, y) == s_xy else 0
        t = x - y - k                          # 앞 점이 가져야 할 u
        if v == 0 and t in gx:
            xs, pre = gx[t], gf[t]
            v = (pre[bisect_left(xs, x)] - pre[bisect_right(xs, x - k)]) % MOD   # x가 (x − k, x)
        f[(x, y)] = v
        gx[x - y].append(x)
        gf[x - y].append((gf[x - y][-1] + v) % MOD)

    # g: 이 점에서 E까지 가는 사슬 수. x가 큰 점부터, 앞 점 구간에 값을 밀어 준다(차분 배열)
    add = {u: [0] * len(xs) for u, xs in gx.items()}   # 값 = 이 칸부터 끝까지 add의 합
    run = {u: 0 for u in gx}
    ptr = {u: len(xs) - 1 for u, xs in gx.items()}
    g = {}
    for x, y, k in reversed(pts):
        u = x - y
        i = bisect_left(gx[u], x)
        a, r, p = add[u], run[u], ptr[u]
        while p >= i:                          # 이 칸까지 내려오며 차분을 더한다
            r += a[p]
            p -= 1
        run[u], ptr[u] = r % MOD, p
        v = 1 if (x, y) == e_xy else r % MOD
        g[(x, y)] = v
        t = u - k
        if v and t in gx:                      # 이 점으로 들어오는 앞 점들: 무리 t, x가 (x − k, x)
            xs = gx[t]
            lo, hi = bisect_right(xs, x - k), bisect_left(xs, x) - 1
            if lo <= hi:
                add[t][hi] += v
                if lo >= 1:
                    add[t][lo - 1] -= v

    total = f[e_xy]
    if table is not None:
        table.update({xy: (f[xy], g[xy]) for xy in f})

    # 새 점 Q 뒤에 올 수 있는 점 R: u_R − k_R = u_Q이고 x_R − k_R < x_Q < x_R
    starts, ends = defaultdict(list), defaultdict(list)
    for x, y, k in pts:
        if k > 0:
            w = x - y - k
            starts[w].append((x - k, g[(x, y)]))
            ends[w].append((x, g[(x, y)]))

    def prefix(items):
        items.sort()
        keys, sums = [], [0]
        for key, val in items:
            keys.append(key)
            sums.append((sums[-1] + val) % MOD)
        return keys, sums

    starts = {w: prefix(v) for w, v in starts.items()}
    ends = {w: prefix(v) for w, v in ends.items()}

    answer = [total]
    for kind, x, y, k in query:
        if kind == 1:                          # 원래 점을 뺀다: 그 점을 지나는 사슬을 뺀다
            answer.append((total - f[(x, y)] * g[(x, y)]) % MOD)
            continue
        u = x - y
        before = 0
        t = u - k
        if t in gx:
            xs, pre = gx[t], gf[t]
            before = (pre[bisect_left(xs, x)] - pre[bisect_right(xs, x - k)]) % MOD
        after = 0
        if u in starts:
            keys, sums = starts[u]
            after += sums[bisect_left(keys, x)]          # x_R − k_R < x
            keys, sums = ends[u]
            after -= sums[bisect_right(keys, x)]         # x_R ≤ x는 뺀다
        answer.append((total + before * after) % MOD)
    return answer


def count(points, s_xy, e_xy):
    """사슬 수를 이중 반복으로 센다(작은 입력만)."""
    pts = sorted(points)
    if s_xy not in [p[:2] for p in pts] or e_xy not in [p[:2] for p in pts]:
        return 0
    f = {}
    for j, (xq, yq, kq) in enumerate(pts):
        v = 1 if (xq, yq) == s_xy else 0
        for xp, yp, _ in pts[:j]:
            if xp < xq and yp > yq and (xq - xp) + (yp - yq) == kq:
                v += f[(xp, yp)]
        f[(xq, yq)] = v
    return f[e_xy] % MOD


def by_recount(n, point, query):
    pts = [tuple(p) for p in point]
    s_xy = min(pts)[:2]
    e_xy = max(pts)[:2]
    out = [count(pts, s_xy, e_xy)]
    for kind, x, y, k in query:
        if kind == 0:
            out.append(count(pts + [(x, y, k)], s_xy, e_xy))
        else:
            out.append(count([p for p in pts if p[:2] != (x, y)], s_xy, e_xy))
    return out


def random_case(n, rng, span):
    xs = rng.sample(range(1, span), n - 2)
    ys = rng.sample(range(1, span), n - 2)
    inner = list(zip(xs, ys))
    pts = [(0, span, 0)] + [(x, y, 0) for x, y in inner] + [(span, 0, 0)]
    out = []
    for i, (x, y, _) in enumerate(pts):
        ups = [(px, py) for px, py, _ in pts if px < x and py > y]
        if ups and rng.random() < 0.85:
            px, py = rng.choice(ups)
            k = (x - px) + (py - y)            # 사슬이 생기도록 앞 점 하나에 맞춘다
        else:
            k = rng.randint(-2, 2 * span)
        out.append([x, y, k])
    used_x = {p[0] for p in out}
    used_y = {p[1] for p in out}
    query = []
    for _ in range(n):
        if rng.random() < 0.5:
            x, y, _ = rng.choice(out)
            query.append([1, x, y, 0])
        else:
            while True:
                x, y = rng.randint(-2, span + 2), rng.randint(-2, span + 2)
                if x not in used_x and y not in used_y:
                    break
            ups = [(px, py) for px, py, _ in out if px < x and py > y]
            k = (x - ups[0][0]) + (ups[0][1] - y) if ups and rng.random() < 0.7 else rng.randint(1, 2 * span)
            query.append([0, x, y, k])
    return out, query


if __name__ == "__main__":
    ex_pts = [[0, 4, 1], [2, 2, 4], [4, 0, 4]]
    ex_q = [[0, 3, 3, 4], [0, 3, 1, 2], [1, 2, 2, 0]]
    tb = {}
    assert solution(3, ex_pts, ex_q, tb) == [1, 2, 1, 0] == by_recount(3, ex_pts, ex_q)
    assert tb == {(0, 4): (1, 1), (2, 2): (1, 1), (4, 0): (1, 1)}
    # 6단계 추적용 예
    pts6 = [[0, 9, 0], [2, 6, 5], [3, 7, 5], [5, 5, 4], [6, 2, 4], [7, 3, 8], [9, 0, 5]]
    q6 = [[1, 5, 5, 0], [0, 8, 4, 4], [1, 0, 9, 0]]
    tb = {}
    assert solution(7, pts6, q6, tb) == by_recount(7, pts6, q6) == [4, 2, 6, 0]
    assert tb == {(0, 9): (1, 4), (2, 6): (1, 2), (3, 7): (1, 2), (5, 5): (2, 1),
                  (6, 2): (2, 1), (7, 3): (2, 1), (9, 0): (4, 1)}
    rng = random.Random(1842)
    for _ in range(1500):
        n = rng.randint(2, 9)
        pts, q = random_case(n, rng, rng.choice([12, 30]))
        assert solution(n, pts, q) == by_recount(n, pts, q), (pts, q)
    # 10만 개
    n = 100_000
    xs = rng.sample(range(1, 10 ** 9), n - 2)
    ys = rng.sample(range(1, 10 ** 9), n - 2)
    pts = [[0, 10 ** 9, 0]] + [[x, y, rng.choice([3, 5, 8, 10 ** 6, 10 ** 8])] for x, y in zip(sorted(xs), sorted(ys, reverse=True))] + [[10 ** 9, 0, 0]]
    q = [[1, p[0], p[1], 0] for p in rng.sample(pts, n // 2)] + [[0, -5 - i, 10 ** 9 + 5 + i, 7] for i in range(n - n // 2)]
    stair = [[i, n - i, 2] for i in range(n)]               # 한 칸씩 내려가는 계단: 사슬이 길다
    stair_q = [[1, i, n - i, 0] for i in range(n)]
    t0 = time.perf_counter()
    solution(n, pts, q)
    res = solution(n, stair, stair_q)
    t = time.perf_counter() - t0
    assert res[0] == 1 and res[1:] == [0] * n
    assert t < 20, t
    print(f"점 10만 개, 변화 10만 개: {t:.2f}s")
    print("ALL CHECKS PASSED")
