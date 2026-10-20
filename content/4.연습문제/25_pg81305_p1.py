"""시험장 나누기 (프로그래머스 81305) 풀이와 검증."""
import math
import random
import time
from itertools import combinations


def children_first(links):
    """자식이 부모보다 먼저 나오는 순서."""
    n = len(links)
    is_child = [False] * n
    for l, r in links:
        if l != -1:
            is_child[l] = True
        if r != -1:
            is_child[r] = True
    root = is_child.index(False)
    order, stack = [], [root]
    while stack:                               # 뿌리부터 내려가는 순서
        v = stack.pop()
        order.append(v)
        for c in links[v]:
            if c != -1:
                stack.append(c)
    return order[::-1]


def groups_needed(limit, num, links, order, cut_side="big"):
    up = [0] * len(num)                        # up[v]: v의 덩어리 중 부모 쪽으로 이어지는 인원
    cnt = 1
    for v in order:
        l, r = links[v]
        a = up[l] if l != -1 else 0
        b = up[r] if r != -1 else 0
        keep = min(a, b) if cut_side == "big" else b   # 흔한 실수 확인용: 늘 왼쪽을 끊는다
        if num[v] + a + b <= limit:            # 둘 다 붙인다
            up[v] = num[v] + a + b
        elif num[v] + keep <= limit:           # 큰 쪽을 끊는다
            up[v] = num[v] + keep
            cnt += 1
        else:                                  # 둘 다 끊는다
            up[v] = num[v]
            cnt += 2
    return cnt, up


def solution(k, num, links, cut_side="big", exact=False, trace=None):
    order = children_first(links)
    lo, hi = max(num), sum(num)
    while lo < hi:
        mid = (lo + hi) // 2
        cnt = groups_needed(mid, num, links, order, cut_side)[0]
        if trace is not None:
            trace.append((lo, hi, mid, cnt))
        if (cnt == k) if exact else (cnt <= k):
            hi = mid
        else:
            lo = mid + 1
    return lo


def by_cuts(k, num, links):
    """끊을 간선 k − 1개를 모두 골라 본다(작은 입력만)."""
    n = len(num)
    edges = [(v, c) for v in range(n) for c in links[v] if c != -1]
    best = None
    for cut in combinations(range(len(edges)), k - 1):
        cut = set(cut)
        adj = [[] for _ in range(n)]
        for i, (u, w) in enumerate(edges):
            if i not in cut:
                adj[u].append(w)
                adj[w].append(u)
        seen, worst = [False] * n, 0
        for s in range(n):
            if not seen[s]:
                seen[s] = True
                stack, tot = [s], 0
                while stack:
                    v = stack.pop()
                    tot += num[v]
                    for w in adj[v]:
                        if not seen[w]:
                            seen[w] = True
                            stack.append(w)
                worst = max(worst, tot)
        best = worst if best is None else min(best, worst)
    return best


def random_tree(n, rng):
    """번호를 섞은 무작위 이진 트리."""
    ids = list(range(n))
    rng.shuffle(ids)
    links = [[-1, -1] for _ in range(n)]
    free = [(ids[0], 0), (ids[0], 1)]          # 자식을 달 수 있는 빈자리
    for v in ids[1:]:
        p, side = free.pop(rng.randrange(len(free)))
        links[p][side] = v
        free += [(v, 0), (v, 1)]
    return links


if __name__ == "__main__":
    tree = [[-1, -1], [-1, -1], [-1, 0], [2, 1]]
    exs = [
        (3, [12, 30, 1, 8, 8, 6, 20, 7, 5, 10, 4, 1],
         [[-1, -1], [-1, -1], [-1, -1], [-1, -1], [8, 5], [2, 10], [3, 0], [6, 1], [11, -1], [7, 4], [-1, -1], [-1, -1]], 40),
        (1, [6, 9, 7, 5], tree, 27),
        (2, [6, 9, 7, 5], tree, 14),
        (4, [6, 9, 7, 5], tree, 9),
    ]
    for k, num, links, want in exs:
        assert solution(k, num, links) == want == by_cuts(k, num, links), (k, want)
    # 6단계 추적: 예시 3 (k = 2)
    tr = []
    assert solution(2, [6, 9, 7, 5], tree, trace=tr) == 14
    assert tr == [(9, 27, 18, 2), (9, 18, 13, 3), (14, 18, 16, 2), (14, 16, 15, 2), (14, 15, 14, 2)]
    order = children_first(tree)
    assert order == [0, 2, 1, 3]
    assert groups_needed(18, [6, 9, 7, 5], tree, order)[1] == [6, 9, 13, 14]
    assert groups_needed(13, [6, 9, 7, 5], tree, order)[1] == [6, 9, 13, 5]
    # 2단계: n = 10,000, k = 5,000일 때 끊는 방법의 수
    assert len(str(math.comb(9_999, 4_999))) == 3_008
    rng = random.Random(81305)
    for _ in range(1500):
        n = rng.randint(1, 10)
        k = rng.randint(1, n)
        num = [rng.randint(1, rng.choice([5, 30, 10_000])) for _ in range(n)]
        links = random_tree(n, rng)
        assert solution(k, num, links) == by_cuts(k, num, links), (k, num, links)
    # 7단계의 흔한 실수: 늘 왼쪽을 끊기, 그룹 수를 정확히 k로 비교하기
    wrong_left = wrong_exact = 0
    for _ in range(1500):
        n = rng.randint(2, 10)
        k = rng.randint(1, n)
        num = [rng.randint(1, 30) for _ in range(n)]
        links = random_tree(n, rng)
        right = solution(k, num, links)
        wrong_left += solution(k, num, links, cut_side="left") != right
        wrong_exact += solution(k, num, links, exact=True) != right
    assert wrong_left > 0 and wrong_exact > 0, (wrong_left, wrong_exact)
    # 1만 개: 한 줄로 늘어진 트리와 무작위 트리
    chain = [[i + 1, -1] for i in range(9_999)] + [[-1, -1]]
    t0 = time.perf_counter()
    for k in (1, 7, 5_000, 10_000):
        solution(k, [rng.randint(1, 10_000) for _ in range(10_000)], chain)
        solution(k, [rng.randint(1, 10_000) for _ in range(10_000)], random_tree(10_000, rng))
    t = time.perf_counter() - t0
    assert solution(10_000, [3] * 10_000, chain) == 3 and solution(1, [3] * 10_000, chain) == 30_000
    assert t < 20, t
    print(f"시험장 1만 개 8번: {t:.2f}s")
    print("ALL CHECKS PASSED")
