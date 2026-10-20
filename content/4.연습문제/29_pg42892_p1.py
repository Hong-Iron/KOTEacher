"""길 찾기 게임 (프로그래머스 42892) 풀이와 검증."""
import random
import sys
import time


def build(nodeinfo):
    nodes = sorted(range(len(nodeinfo)), key=lambda i: (-nodeinfo[i][1], nodeinfo[i][0]))   # 위층부터
    left, right = {}, {}
    root = nodes[0]
    for i in nodes[1:]:                        # x를 열쇠로 이진 탐색 트리에 넣는다
        cur = root
        while True:
            if nodeinfo[i][0] < nodeinfo[cur][0]:
                if cur not in left:
                    left[cur] = i
                    break
                cur = left[cur]
            else:
                if cur not in right:
                    right[cur] = i
                    break
                cur = right[cur]
    return root, left, right, nodes


def solution(nodeinfo):
    root, left, right, _ = build(nodeinfo)
    pre, post = [], []
    stack = [root]                             # 전위: 뿌리 → 왼쪽 → 오른쪽
    while stack:
        v = stack.pop()
        pre.append(v + 1)
        if v in right:
            stack.append(right[v])
        if v in left:
            stack.append(left[v])
    stack = [root]                             # 후위: (뿌리 → 오른쪽 → 왼쪽)을 뒤집는다
    while stack:
        v = stack.pop()
        post.append(v + 1)
        if v in left:
            stack.append(left[v])
        if v in right:
            stack.append(right[v])
    post.reverse()
    return [pre, post]


def by_split(nodeinfo):
    """y가 가장 큰 점을 뿌리로, x로 왼쪽·오른쪽을 나눠 재귀로 만든다."""
    sys.setrecursionlimit(10_000)
    pre, post = [], []

    def go(ids):
        if not ids:
            return
        r = max(ids, key=lambda i: nodeinfo[i][1])
        L = [i for i in ids if nodeinfo[i][0] < nodeinfo[r][0]]
        R = [i for i in ids if nodeinfo[i][0] > nodeinfo[r][0]]
        pre.append(r + 1)
        go(L)
        go(R)
        post.append(r + 1)

    go(list(range(len(nodeinfo))))
    return [pre, post]


def random_tree(rng, n):
    """모양이 무작위인 이진 트리를 만들고, 중위 순서로 x를, 깊이로 y를 준다."""
    left, right = {}, {}
    for v in range(1, n):
        cur = 0
        while True:
            side = rng.random() < 0.5
            d = left if side else right
            if cur not in d:
                d[cur] = v
                break
            cur = d[cur]
    depth, order = {0: 0}, []

    def walk(v):
        if v in left:
            depth[left[v]] = depth[v] + 1
            walk(left[v])
        order.append(v)
        if v in right:
            depth[right[v]] = depth[v] + 1
            walk(right[v])

    walk(0)
    xs = sorted(rng.sample(range(0, max(100, 10 * n)), n))
    maxd = max(depth.values())
    info = [None] * n
    for rank, v in enumerate(order):
        info[v] = [xs[rank], maxd - depth[v]]
    perm = list(range(n))
    rng.shuffle(perm)
    return [info[p] for p in perm]


if __name__ == "__main__":
    ex = [[5, 3], [11, 5], [13, 3], [3, 5], [6, 1], [1, 3], [8, 6], [7, 2], [2, 2]]
    assert solution(ex) == [[7, 4, 6, 9, 1, 8, 5, 2, 3], [9, 6, 5, 8, 1, 4, 3, 2, 7]] == by_split(ex)
    # 6단계 추적: 넣는 순서와 자리(번호는 1부터)
    root, L, R, order = build(ex)
    assert [i + 1 for i in order] == [7, 4, 2, 6, 1, 3, 9, 8, 5]
    kids = {v + 1: (L.get(v, -1) + 1 or None, R.get(v, -1) + 1 or None) for v in range(9)}
    assert kids == {7: (4, 2), 4: (6, 1), 2: (None, 3), 6: (None, 9), 1: (None, 8), 8: (5, None),
                    3: (None, None), 9: (None, None), 5: (None, None)}, kids
    rng = random.Random(42892)
    for _ in range(1500):
        info = random_tree(rng, rng.randint(1, 20))
        assert solution(info) == by_split(info), info
    # 깊이 1,000인 한 줄 나무: 반복문이라 재귀 한도와 상관없다
    chain = [[50_000 - i * 10, 1000 - i] for i in range(1000)]
    res = solution(chain)
    assert res[0] == list(range(1, 1001)) and res[1] == list(range(1000, 0, -1))
    # 노드 1만 개
    big = random_tree(rng, 10_000)
    t0 = time.perf_counter()
    assert solution(big) == by_split(big)
    print(f"n=10000: {time.perf_counter() - t0:.2f}s")
    print("ALL CHECKS PASSED")
