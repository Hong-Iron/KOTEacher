"""29.트리 순회와 이진 탐색 트리: 순회 세 가지, BST 넣기·찾기, 문서 주장의 확인."""
import random
import sys


class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


def insert(root, key):
    """반복문으로 넣는다. 새 뿌리를 돌려준다."""
    node = Node(key)
    if root is None:
        return node
    cur = root
    while True:
        if key < cur.key:
            if cur.left is None:
                cur.left = node
                return root
            cur = cur.left
        else:
            if cur.right is None:
                cur.right = node
                return root
            cur = cur.right


def find(root, key):
    cur, steps = root, 0
    while cur is not None:
        steps += 1
        if key == cur.key:
            return True, steps
        cur = cur.left if key < cur.key else cur.right
    return False, steps


def preorder(n, out):
    if n:
        out.append(n.key)
        preorder(n.left, out)
        preorder(n.right, out)
    return out


def inorder(n, out):
    if n:
        inorder(n.left, out)
        out.append(n.key)
        inorder(n.right, out)
    return out


def postorder(n, out):
    if n:
        postorder(n.left, out)
        postorder(n.right, out)
        out.append(n.key)
    return out


def inorder_iter(root):
    """스택으로 짠 중위 순회(재귀 한도를 피할 때)."""
    out, stack, cur = [], [], root
    while stack or cur:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        out.append(cur.key)
        cur = cur.right
    return out


def height(n):
    """간선 수로 센 높이. 빈 나무는 -1."""
    if n is None:
        return -1
    return 1 + max(height(n.left), height(n.right))


def build(keys):
    root = None
    for k in keys:
        root = insert(root, k)
    return root


if __name__ == "__main__":
    # 예시로 보기
    r = build([5, 3, 8, 1, 4, 7, 9])
    assert preorder(r, []) == [5, 3, 1, 4, 8, 7, 9]
    assert inorder(r, []) == [1, 3, 4, 5, 7, 8, 9]
    assert postorder(r, []) == [1, 4, 3, 7, 9, 8, 5]
    assert height(r) == 2
    assert find(r, 7) == (True, 3) and find(r, 6) == (False, 3)
    # 정렬된 순서로 넣으면 한 줄로 늘어진다
    chain = build([1, 2, 3, 4, 5])
    assert height(chain) == 4 and find(chain, 5) == (True, 5)
    # C1: 넣는 순서 [6, 2, 9, 1, 4, 8, 3]
    c = build([6, 2, 9, 1, 4, 8, 3])
    assert preorder(c, []) == [6, 2, 1, 4, 3, 9, 8]
    assert inorder(c, []) == [1, 2, 3, 4, 6, 8, 9]
    assert postorder(c, []) == [1, 3, 4, 2, 8, 9, 6]
    # C3: 전위·후위가 같은데 모양이 다른 두 나무 (1의 왼쪽 자식 2 / 오른쪽 자식 2)
    a = Node(1); a.left = Node(2)
    b = Node(1); b.right = Node(2)
    assert (preorder(a, []), postorder(a, [])) == (preorder(b, []), postorder(b, [])) == ([1, 2], [2, 1])
    assert inorder(a, []) != inorder(b, [])
    # 포화 이진 트리를 중위 순서로 늘어놓으면 뿌리는 한가운데(2^h - 1개 중 가운데)
    for h in range(1, 6):
        size = 2 ** h - 1
        perfect = build([])
        # 가운데부터 넣으면 포화 이진 트리가 된다
        def mid_order(lo, hi, acc):
            if lo > hi:
                return acc
            m = (lo + hi) // 2
            acc.append(m)
            mid_order(lo, m - 1, acc)
            mid_order(m + 1, hi, acc)
            return acc
        perfect = build(mid_order(0, size - 1, []))
        assert height(perfect) == h - 1 and perfect.key == size // 2
    # 무작위: 중위 순회는 정렬, 반복문 중위 = 재귀 중위, 찾기 = 집합
    rng = random.Random(29)
    for _ in range(2000):
        keys = rng.sample(range(100), rng.randint(0, 30))
        t = build(keys)
        ino = inorder(t, [])
        assert ino == sorted(keys) == inorder_iter(t)
        assert len(preorder(t, [])) == len(postorder(t, [])) == len(keys)
        for q in range(0, 100, 7):
            assert find(t, q)[0] == (q in set(keys))
    # 깊이 1,000인 나무의 재귀: 기본 한도(1,000)에서는 넘칠 수 있다
    deep = build(list(range(1000)))
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(1000)                                   # 파이썬 기본값
    try:
        preorder(deep, [])
        raise AssertionError("RecursionError가 나야 한다")
    except RecursionError:
        pass
    sys.setrecursionlimit(10_000)
    assert len(preorder(deep, [])) == 1000 and inorder_iter(deep) == list(range(1000))
    sys.setrecursionlimit(old)
    print("ALL CHECKS PASSED")
