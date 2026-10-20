"""이분 매칭: 문서의 실행 추적, 확인 문제 답, 무작위 비교."""
import random
from itertools import combinations, permutations


def max_matching(adj, n_right, log=None):
    """왼쪽 정점마다 증가 경로를 찾아 짝을 늘린다(쿤의 방법)."""
    match = [-1] * n_right                     # 오른쪽 정점 → 짝인 왼쪽 정점

    def try_(u, seen):
        for v in adj[u]:
            if v in seen:
                continue
            seen.add(v)
            if match[v] == -1 or try_(match[v], seen):   # 비어 있거나, 주인이 다른 데로 옮길 수 있으면
                if log is not None:
                    log.append((u, v))
                match[v] = u
                return True
        return False

    size = 0
    for u in range(len(adj)):
        if try_(u, set()):                     # 왼쪽 정점마다 seen을 새로 만든다
            size += 1
    return size, match


def greedy(adj, n_right):
    """흔한 실수: 먼저 온 사람에게 빈자리를 주고 다시 바꾸지 않는다."""
    taken, size = set(), 0
    for u in range(len(adj)):
        for v in adj[u]:
            if v not in taken:
                taken.add(v)
                size += 1
                break
    return size


def by_subsets(adj):
    edges = [(u, v) for u in range(len(adj)) for v in adj[u]]
    for k in range(min(len(adj), len(edges)), 0, -1):
        for pick in combinations(edges, k):
            if len({u for u, _ in pick}) == k and len({v for _, v in pick}) == k:
                return k
    return 0


def best_matching(w):
    """가중치가 있는 짝짓기(헝가리안 방법). 신비로운 유적 탐험 풀이의 것과 같다."""
    if not w or not w[0]:
        return 0
    if len(w) > len(w[0]):
        w = [list(col) for col in zip(*w)]
    n, m = len(w), len(w[0])
    INF = float("inf")
    u, v, match, way = [0] * (n + 1), [0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        match[0], j0 = i, 0
        minv, used = [INF] * (m + 1), [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = match[j0], INF, 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = -w[i0 - 1][j - 1] - u[i0] - v[j]
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
        while j0:
            j1 = way[j0]
            match[j0] = match[j1]
            j0 = j1
    return sum(w[match[j] - 1][j - 1] for j in range(1, m + 1) if match[j])


if __name__ == "__main__":
    # 예시: 학생 0, 1, 2 / 동아리 a=0, b=1, c=2
    adj = [[0, 1], [0], [1, 2]]
    log = []
    size, match = max_matching(adj, 3, log)
    assert size == 3 and match == [1, 0, 2]
    assert log == [(0, 0), (0, 1), (1, 0), (2, 2)]     # 1번 학생이 b로 옮겨 2번에게 a를 내준다
    # 확인 문제 C3: 욕심껏 주면 1명, 최대는 2명
    assert greedy([[0, 1], [0]], 2) == 1 and max_matching([[0, 1], [0]], 2)[0] == 2
    # 확인 문제 C1: 학생 3이 b만 원하면
    assert max_matching([[0, 1], [0], [1]], 3)[0] == 2
    rng = random.Random(34)
    for _ in range(2000):
        nl, nr = rng.randint(1, 6), rng.randint(1, 6)
        adj = [sorted(rng.sample(range(nr), rng.randint(0, nr))) for _ in range(nl)]
        want = by_subsets(adj)
        got, match = max_matching(adj, nr)
        assert got == want, adj
        assert all(m == -1 or v in adj[m] for v, m in enumerate(match))
        assert len([m for m in match if m != -1]) == len({m for m in match if m != -1}) == got
    # 가중치가 있는 짝짓기: 순열 전부와 비교
    for _ in range(1000):
        r, c = rng.randint(1, 5), rng.randint(1, 5)
        w = [[rng.randint(0, 9) for _ in range(c)] for _ in range(r)]
        if r <= c:
            want = max(sum(w[i][p[i]] for i in range(r)) for p in permutations(range(c), r))
        else:
            want = max(sum(w[p[j]][j] for j in range(c)) for p in permutations(range(r), c))
        assert best_matching(w) == want
    assert best_matching([[3, 2], [2, 0]]) == 4 and best_matching([[2, 3], [3, 3]]) == 6
    print("ALL CHECKS PASSED")
