"""신비로운 유적 탐험 (프로그래머스 1834) 풀이와 검증. 노드 번호는 문제처럼 1부터 센다."""
import random
import time
from itertools import permutations


def best_matching(w):
    """w[i][j] ≥ 0인 표에서, 행과 열을 겹치지 않게 짝지어 얻는 값의 합의 최댓값(헝가리안 방법)."""
    if not w or not w[0]:
        return 0
    if len(w) > len(w[0]):
        w = [list(col) for col in zip(*w)]     # 행이 열보다 많지 않게 돌린다
    n, m = len(w), len(w[0])
    INF = float("inf")
    u, v = [0] * (n + 1), [0] * (m + 1)        # 행과 열의 잠재값
    match = [0] * (m + 1)                      # 열 j와 짝인 행 (0이면 없음)
    way = [0] * (m + 1)
    for i in range(1, n + 1):                  # 행을 하나씩 짝에 넣는다
        match[0] = i
        j0 = 0
        minv = [INF] * (m + 1)
        used = [False] * (m + 1)
        while True:                            # 가장 싸게 늘리는 길을 찾는다
            used[j0] = True
            i0, delta, j1 = match[j0], INF, 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = -w[i0 - 1][j - 1] - u[i0] - v[j]     # 값을 비용(−값)으로 바꿔 최소화
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(m + 1):
                if used[j]:
                    u[match[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if match[j0] == 0:
                break
        while j0:                              # 찾은 길을 따라 짝을 바꾼다
            j1 = way[j0]
            match[j0] = match[j1]
            j0 = j1
    return sum(w[match[j] - 1][j - 1] for j in range(1, m + 1) if match[j])


def children_lists(n, g):
    adj = [[] for _ in range(n + 1)]
    for p, q in g:
        adj[p].append(q)
        adj[q].append(p)
    kids = [[] for _ in range(n + 1)]
    order, seen, stack = [], [False] * (n + 1), [1]
    seen[1] = True
    while stack:                               # 뿌리 1부터 내려가며 부모-자식을 정한다
        v = stack.pop()
        order.append(v)
        for c in adj[v]:
            if not seen[c]:
                seen[c] = True
                kids[v].append(c)
                stack.append(c)
    return kids, order[::-1]                   # 자식이 먼저인 순서


def solution(n1, g1, n2, g2, table=None):
    kids1, order1 = children_lists(n1, g1)
    kids2, order2 = children_lists(n2, g2)
    dp = [[0] * (n2 + 1) for _ in range(n1 + 1)]   # dp[u][v]: u와 v를 뿌리로 맞출 때 공통부분 크기
    for u in order1:
        for v in order2:
            w = [[dp[c][d] for d in kids2[v]] for c in kids1[u]]
            dp[u][v] = 1 + best_matching(w)
    if table is not None:
        table.extend(dp)
    return dp[1][1]


def canon(kids, v, keep):
    """keep 안의 v 아래 나무를 순서 없는 꼴로 적는다."""
    return "(" + "".join(sorted(canon(kids, c, keep) for c in kids[v] if c in keep)) + ")"


def rooted_subtrees(n, g):
    kids, _ = children_lists(n, g)
    parent = {c: v for v in range(1, n + 1) for c in kids[v]}
    shapes = {}
    for mask in range(1 << (n - 1)):           # 뿌리 1은 늘 넣는다
        keep = {1} | {i + 2 for i in range(n - 1) if mask >> i & 1}
        if all(parent[x] in keep for x in keep if x != 1):
            shapes[canon(kids, 1, keep)] = len(keep)
    return shapes


def by_shapes(n1, g1, n2, g2):
    """뿌리를 포함한 부분 나무의 모양을 모두 적어 겹치는 가장 큰 것을 찾는다(작은 입력만)."""
    s1, s2 = rooted_subtrees(n1, g1), rooted_subtrees(n2, g2)
    return max(s1[k] for k in s1 if k in s2)


def random_tree(n, rng):
    g = [[rng.randint(1, i - 1), i] for i in range(2, n + 1)]
    perm = list(range(2, n + 1))
    rng.shuffle(perm)
    relabel = {1: 1, **{i: perm[i - 2] for i in range(2, n + 1)}}
    return [[relabel[a], relabel[b]] if rng.random() < 0.5 else [relabel[b], relabel[a]] for a, b in g]


if __name__ == "__main__":
    g1 = [[3, 1], [5, 7], [8, 7], [2, 3], [3, 6], [1, 5], [4, 3]]
    g2 = [[1, 5], [5, 6], [3, 7], [3, 1], [7, 4], [7, 2], [9, 8], [5, 9]]
    tb = []
    assert solution(8, g1, 9, g2, tb) == 7 == by_shapes(8, g1, 9, g2)
    assert (tb[3][5], tb[3][3], tb[5][5], tb[5][3], tb[1][1]) == (3, 2, 3, 3, 7)   # 6단계 표
    # 헝가리안 방법을 순열 전부와 비교한다
    rng = random.Random(1834)
    for _ in range(2000):
        r, c = rng.randint(0, 5), rng.randint(0, 5)
        w = [[rng.randint(0, 9) for _ in range(c)] for _ in range(r)]
        if r <= c:
            want = max((sum(w[i][p[i]] for i in range(r)) for p in permutations(range(c), r)), default=0)
        else:
            want = max(sum(w[p[j]][j] for j in range(c)) for p in permutations(range(r), c))
        assert best_matching(w) == want, w
    # 큰 쪽을 욕심으로 고르면 틀리는 표 (7단계)
    assert best_matching([[3, 2], [2, 0]]) == 4 and best_matching([[2, 3], [3, 3]]) == 6
    for _ in range(1500):
        n1, n2 = rng.randint(1, 9), rng.randint(1, 9)
        a, b = random_tree(n1, rng), random_tree(n2, rng)
        assert solution(n1, a, n2, b) == by_shapes(n1, a, n2, b), (a, b)
    # 노드 100개: 별 모양 둘, 한 줄 둘, 무작위 둘
    star = [[1, i] for i in range(2, 101)]
    line = [[i, i + 1] for i in range(1, 100)]
    t0 = time.perf_counter()
    assert solution(100, star, 100, star) == 100
    assert solution(100, line, 100, line) == 100 and solution(100, star, 100, line) == 2
    solution(100, random_tree(100, rng), 100, random_tree(100, rng))
    t = time.perf_counter() - t0
    assert t < 20, t
    print(f"노드 100개 네 번: {t:.2f}s")
    print("ALL CHECKS PASSED")
