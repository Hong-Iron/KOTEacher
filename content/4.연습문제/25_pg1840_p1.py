"""스마트한 프로도 (프로그래머스 1840) 풀이와 검증. 정점·간선 번호는 문제처럼 1부터 센다."""
import random
import time


def solution(n, m, a, b, k, m1, m2, e1, e2, parts=None, shrink_first=False):
    only0 = set(e1) - set(e2)                  # M_0에만 있는 간선: 빼야 한다
    only1 = set(e2) - set(e1)                  # M_t에만 있는 간선: 넣어야 한다
    at0, at1 = {}, {}                          # 정점 → 그 정점에 붙은 only0 간선, only1 간선
    for e in only0:
        at0[a[e - 1]] = at0[b[e - 1]] = e
    for e in only1:
        at1[a[e - 1]] = at1[b[e - 1]] = e

    def other(e, v):
        return b[e - 1] if a[e - 1] == v else a[e - 1]

    seen = set()

    def walk(v, e):
        """정점 v에서 간선 e로 출발해, 두 종류를 번갈아 밟으며 간다."""
        seq = []
        while e is not None and e not in seen:
            seen.add(e)
            seq.append(e)
            v = other(e, v)
            e = (at1 if e in only0 else at0).get(v)
        return seq

    comps = []                                 # (경로인가, 간선 순서)
    for v in set(at0) | set(at1):              # 끝점(한 종류만 붙은 정점)에서 경로를 딴다
        if (v in at0) != (v in at1):
            e = at0.get(v) or at1.get(v)
            if e not in seen:
                comps.append((True, walk(v, e)))
    for e in list(only0) + list(only1):        # 남은 것은 사이클이다
        if e not in seen:
            comps.append((False, walk(a[e - 1], e)))

    grow, even, shrink = [], [], []
    for is_path, seq in comps:
        c0 = sum(e in only0 for e in seq)
        c1 = len(seq) - c0
        if is_path and seq[0] in only0 and seq[-1] in only1:
            seq.reverse()                      # 넣을 간선이 있는 끝에서 시작한다
        (grow if c1 > c0 else even if c1 == c0 else shrink).append((is_path, seq))
    if parts is not None:
        parts.extend([len(grow), len(even), len(shrink)])

    steps = []
    order = shrink + even + grow if shrink_first else grow + even + shrink   # 앞의 것은 흔한 실수 확인용
    for is_path, seq in order:                 # 커지는 것 → 그대로인 것 → 작아지는 것
        size = len(seq)

        def nbrs(i):
            out = []
            if i > 0 or not is_path:
                out.append(seq[i - 1])
            if i < size - 1:
                out.append(seq[i + 1])
            elif not is_path:
                out.append(seq[0])
            return out

        block = {}                             # 넣을 간선 → 아직 남아 있는 이웃 only0 간선 수
        for i, e in enumerate(seq):
            if e in only1:
                block[e] = sum(f in only0 for f in nbrs(i))
                if block[e] == 0:
                    steps.append([1, e])       # 막는 간선이 없으면 바로 넣는다
        for i, e in enumerate(seq):
            if e in only0:
                steps.append([0, e])
                for f in nbrs(i):
                    if f in only1:
                        block[f] -= 1
                        if block[f] == 0:
                            steps.append([1, f])
    return steps


def check(n, a, b, k, e1, e2, steps):
    """단계마다 매칭인지, 중간 크기가 k − 2 이상인지, 끝이 M_t인지 본다. 가장 작았던 크기를 돌려준다."""
    cur = set(e1)
    used = {}
    for e in cur:
        for v in (a[e - 1], b[e - 1]):
            assert v not in used
            used[v] = e
    low = len(cur)
    for i, (kind, e) in enumerate(steps):
        if kind == 0:
            assert e in cur
            cur.remove(e)
            del used[a[e - 1]], used[b[e - 1]]
        else:
            assert kind == 1 and e not in cur
            assert a[e - 1] not in used and b[e - 1] not in used, "매칭이 깨진다"
            cur.add(e)
            used[a[e - 1]] = used[b[e - 1]] = e
        if i < len(steps) - 1:
            assert len(cur) >= k - 2, (i, len(cur), k)
            low = min(low, len(cur))
    assert cur == set(e2)
    return low


def random_matching(m, a, b, rng, p):
    order = list(range(1, m + 1))
    rng.shuffle(order)
    used, out = set(), []
    for e in order:
        if a[e - 1] not in used and b[e - 1] not in used and rng.random() < p:
            used |= {a[e - 1], b[e - 1]}
            out.append(e)
    return out


if __name__ == "__main__":
    a, b = [1, 1, 2, 2, 3, 4], [2, 3, 3, 4, 5, 5]
    steps = solution(5, 6, a, b, 2, 2, 2, [3, 6], [2, 4])
    assert steps == [[0, 3], [1, 2], [0, 6], [1, 4]], steps
    assert check(5, a, b, 2, [3, 6], [2, 4], steps) == 1
    # 6단계 추적: 커지는 경로, 그대로인 경로와 사이클, 작아지는 경로, 함께 있는 간선 하나
    a6 = [1, 2, 3, 5, 6, 8, 9, 10, 11, 12, 13, 14, 16]
    b6 = [2, 3, 4, 6, 7, 9, 10, 11, 8, 13, 14, 15, 17]
    e1_6, e2_6 = [2, 4, 6, 8, 10, 12, 13], [1, 3, 5, 7, 9, 11, 13]
    parts = []
    steps6 = solution(17, 13, a6, b6, 7, 7, 7, e1_6, e2_6, parts)
    assert parts == [1, 2, 1]
    assert steps6 == [[0, 2], [1, 1], [1, 3], [0, 4], [1, 5], [0, 6], [0, 8], [1, 7], [1, 9],
                      [0, 10], [0, 12], [1, 11]], steps6
    assert check(17, a6, b6, 7, e1_6, e2_6, steps6) == 6
    # 2단계: 다 빼고 다 넣으면 크기가 1까지 떨어진다
    naive = [[0, e] for e in e1_6 if e not in e2_6] + [[1, e] for e in e2_6 if e not in e1_6]
    try:
        check(17, a6, b6, 7, e1_6, e2_6, naive)
        raise RuntimeError("실수가 드러나지 않았다")
    except AssertionError:
        pass
    assert len(set(e1_6) & set(e2_6)) == 1
    # 7단계의 흔한 실수: 작아지는 것부터 하면 k − 2 아래로 내려간다
    a7 = [1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15]
    b7 = [2, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 16]
    e1_7, e2_7 = [1, 3, 4, 6, 8, 11], [2, 5, 7, 9, 10, 12]
    assert check(16, a7, b7, 6, e1_7, e2_7, solution(16, 12, a7, b7, 6, 6, 6, e1_7, e2_7)) == 5
    size, low = 6, 6
    bad = solution(16, 12, a7, b7, 6, 6, 6, e1_7, e2_7, shrink_first=True)
    for kind, _ in bad[:-1]:
        size += 1 if kind else -1
        low = min(low, size)
    assert low == 3
    try:
        check(16, a7, b7, 6, e1_7, e2_7, bad)
        raise RuntimeError("실수가 드러나지 않았다")
    except AssertionError:
        pass
    rng = random.Random(1840)
    for _ in range(3000):
        n = rng.randint(2, 12)
        pairs = [(u, v) for u in range(1, n + 1) for v in range(u + 1, n + 1)]
        rng.shuffle(pairs)
        pairs = pairs[:rng.randint(1, len(pairs))]
        a = [u for u, _ in pairs]
        b = [v for _, v in pairs]
        m = len(pairs)
        e1 = random_matching(m, a, b, rng, rng.choice([0.5, 1.0]))
        e2 = random_matching(m, a, b, rng, rng.choice([0.5, 1.0]))
        if not e1 or not e2:
            continue
        k = min(len(e1), len(e2))              # 가장 빡빡한 k
        steps = solution(n, m, a, b, k, len(e1), len(e2), e1, e2)
        check(n, a, b, k, e1, e2, steps)
    # 정점 10만 개, 간선 100만 개
    n, m = 100_000, 1_000_000
    a = [rng.randint(1, n) for _ in range(m)]
    b = [rng.randint(1, n) for _ in range(m)]
    for i in range(m):
        if a[i] == b[i]:
            b[i] = a[i] % n + 1
    e1 = random_matching(m, a, b, rng, 1.0)
    e2 = random_matching(m, a, b, rng, 1.0)
    k = min(len(e1), len(e2))
    t0 = time.perf_counter()
    steps = solution(n, m, a, b, k, len(e1), len(e2), e1, e2)
    t = time.perf_counter() - t0
    check(n, a, b, k, e1, e2, steps)
    assert t < 20, t
    print(f"정점 10만, 간선 100만, 매칭 {len(e1)}·{len(e2)}개: {t:.2f}s")
    print("ALL CHECKS PASSED")
