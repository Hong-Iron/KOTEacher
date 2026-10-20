"""15.유니온 파인드: 크기로 합치기와 경로 압축을 쓴 서로소 집합과 문서 주장의 확인."""
import math
import random
from collections import deque


class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        root = x
        while self.parent[root] != root:          # 대표까지 올라간다
            root = self.parent[root]
        while self.parent[x] != root:             # 지나온 칸을 모두 대표에 바로 잇는다(경로 압축)
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if self.size[a] < self.size[b]:           # 작은 무리를 큰 무리 밑에
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        return True


def depth_without_compression(n, pairs, by_size):
    parent, size = list(range(n)), [1] * n

    def root(x):
        d = 0
        while parent[x] != x:
            x = parent[x]
            d += 1
        return x, d

    for a, b in pairs:
        ra, rb = root(a)[0], root(b)[0]
        if ra == rb:
            continue
        if by_size and size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
    return max(root(x)[1] for x in range(n))


def same_by_bfs(n, pairs, a, b):
    g = [[] for _ in range(n)]
    for x, y in pairs:
        g[x].append(y)
        g[y].append(x)
    seen, q = {a}, deque([a])
    while q:
        v = q.popleft()
        for u in g[v]:
            if u not in seen:
                seen.add(u)
                q.append(u)
    return b in seen


if __name__ == "__main__":
    # 예시로 보기: 0 ~ 5, union(0,1), union(2,3), union(1,3), union(4,5)
    d = DSU(6)
    d.union(0, 1)
    assert d.parent == [0, 0, 2, 3, 4, 5]
    d.union(2, 3)
    assert d.parent == [0, 0, 2, 2, 4, 5]
    d.union(1, 3)
    assert d.parent == [0, 0, 0, 2, 4, 5] and d.size[0] == 4
    d.union(4, 5)
    assert d.parent == [0, 0, 0, 2, 4, 4]
    assert d.find(3) == 0 and d.parent[3] == 0                 # 찾으면서 3을 0에 바로 잇는다
    assert d.find(5) != d.find(0)
    # C1: 0 ~ 4, union(3,4), union(1,2), union(2,4), 대표 확인
    c = DSU(5)
    for a, b in ((3, 4), (1, 2), (2, 4)):
        c.union(a, b)
    assert c.parent == [0, 1, 1, 1, 3]
    groups = {}
    for x in range(5):
        groups.setdefault(c.find(x), []).append(x)
    assert sorted(groups.values()) == [[0], [1, 2, 3, 4]]
    # C3: 크기를 보지 않고 늘 두 번째를 첫 번째 밑에 두면 한 줄이 된다
    chain = [(i + 1, i) for i in range(9)]          # union(1,0), union(2,1), … : 지금까지의 무리가 늘 새 칸 밑으로
    assert depth_without_compression(10, chain, by_size=False) == 9
    assert depth_without_compression(10, chain, by_size=True) == 1
    # 크기로 합치면 깊이 ≤ log2 n (경로 압축 없이도)
    rng = random.Random(15)
    for _ in range(500):
        n = rng.randint(1, 64)
        pairs = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 3 * n))]
        assert depth_without_compression(n, pairs, by_size=True) <= math.log2(n) if n > 1 else True
    # 무작위: 같은 무리 판정 = BFS
    for _ in range(1500):
        n = rng.randint(1, 12)
        pairs = [(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 12))]
        ds = DSU(n)
        for a, b in pairs:
            ds.union(a, b)
        for _ in range(8):
            a, b = rng.randrange(n), rng.randrange(n)
            assert (ds.find(a) == ds.find(b)) == same_by_bfs(n, pairs, a, b)
    print("ALL CHECKS PASSED")
