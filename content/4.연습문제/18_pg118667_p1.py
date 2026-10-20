"""두 큐 합 같게 만들기 (프로그래머스 118667) 풀이와 검증."""
import itertools
import random
from collections import deque


def solution(queue1, queue2):
    arr = queue1 + queue2
    n = len(queue1)
    total = sum(arr)
    if total % 2:
        return -1
    target = total // 2
    s = sum(queue1)
    i, j = 0, n
    for count in range(3 * n + 1):
        if s == target:
            return count
        if s > target:
            s -= arr[i % (2 * n)]
            i += 1
        else:
            s += arr[j % (2 * n)]
            j += 1
    return -1


def bfs(q1, q2):
    """가능한 모든 (queue1, queue2) 상태를 BFS로 돈다. 진짜 최솟값."""
    if (sum(q1) + sum(q2)) % 2:
        return -1
    start = (tuple(q1), tuple(q2))
    dist = {start: 0}
    dq = deque([start])
    while dq:
        a, b = dq.popleft()
        if sum(a) == sum(b):
            return dist[(a, b)]
        nxt = []
        if a:
            nxt.append((a[1:], b + (a[0],)))
        if b:
            nxt.append((a + (b[0],), b[1:]))
        for st in nxt:
            if st not in dist:
                dist[st] = dist[(a, b)] + 1
                dq.append(st)
    return -1


if __name__ == "__main__":
    assert solution([3, 2, 7, 2], [4, 6, 5, 1]) == 2
    assert solution([1, 2, 1, 2], [1, 10, 1, 2]) == 7
    assert solution([1, 1], [1, 5]) == -1
    worst = 0
    for n in range(1, 5):
        vals = range(1, 5) if n <= 3 else range(1, 4)
        for q1 in itertools.product(vals, repeat=n):
            for q2 in itertools.product(vals, repeat=n):
                b = bfs(list(q1), list(q2))
                assert solution(list(q1), list(q2)) == b, (q1, q2)
                if b > 0:
                    worst = max(worst, b - (2 * n - 1))
    assert worst <= 0          # 필요한 작업은 많아야 2n - 1
    rng = random.Random(118667)
    for _ in range(3000):
        n = rng.randint(1, 7)
        q1 = [rng.choice([1, 1, 2, 3, 50]) for _ in range(n)]
        q2 = [rng.choice([1, 1, 2, 3, 50]) for _ in range(n)]
        assert solution(q1, q2) == bfs(q1, q2), (q1, q2)
    print("ALL CHECKS PASSED")
