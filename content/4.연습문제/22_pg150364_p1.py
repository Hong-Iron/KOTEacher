"""1,2,3 떨어트리기 (프로그래머스 150364) 풀이와 검증."""
import random
from itertools import product


def solution(edges, target):
    n = len(target)
    children = [[] for _ in range(n + 1)]
    for p, c in edges:
        children[p].append(c)
    for ch in children:
        ch.sort()
    ptr = [0] * (n + 1)                          # 노드마다 지금 길인 자식의 순번
    leaves = [v for v in range(1, n + 1) if not children[v]]
    need = {v: target[v - 1] for v in leaves}
    cnt = {v: 0 for v in leaves}
    order = []                                   # 몇 번째 숫자가 어느 리프에 떨어지나

    def drop():
        v = 1
        while children[v]:
            nxt = children[v][ptr[v]]
            ptr[v] = (ptr[v] + 1) % len(children[v])   # 지나간 노드는 다음 자식으로 길을 바꾼다
            v = nxt
        return v

    while not all(3 * cnt[v] >= need[v] for v in leaves):   # 모든 리프가 3씩 받아도 모자라지 않을 때까지
        leaf = drop()
        cnt[leaf] += 1
        order.append(leaf)
        if cnt[leaf] > need[leaf]:               # 1씩 받아도 넘친다
            return [-1]

    seqs = {}
    for v in leaves:                             # 리프마다 개수 c, 합 t인 사전 순으로 가장 앞선 수열
        c, t, s = cnt[v], need[v], []
        for i in range(c):
            rest = c - i - 1
            for x in (1, 2, 3):
                if rest <= t - x <= 3 * rest:    # 남은 자리로 나머지를 채울 수 있나
                    s.append(x)
                    t -= x
                    break
        seqs[v] = s[::-1]                        # 뒤에서부터 꺼내 쓰려고 뒤집는다
    return [seqs[leaf].pop() for leaf in order]


def by_all_sequences(edges, target):
    """길이를 늘려 가며 1·2·3 수열을 사전 순으로 모두 떨어뜨려 본다(작은 입력만)."""
    n = len(target)
    children = [[] for _ in range(n + 1)]
    for p, c in edges:
        children[p].append(c)
    for ch in children:
        ch.sort()
    for length in range(1, sum(target) + 1):
        for seq in product((1, 2, 3), repeat=length):
            ptr = [0] * (n + 1)
            got = [0] * (n + 1)
            for x in seq:
                v = 1
                while children[v]:
                    nxt = children[v][ptr[v]]
                    ptr[v] = (ptr[v] + 1) % len(children[v])
                    v = nxt
                got[v] += x
            if got[1:] == target:
                return list(seq)
    return [-1]


def random_case(rng, n):
    edges = [[rng.randint(1, v - 1), v] for v in range(2, n + 1)]
    has_child = {p for p, _ in edges}
    target = [0] * n
    for v in range(1, n + 1):
        if v not in has_child:
            target[v - 1] = rng.randint(0, 3)
    if sum(target) == 0:
        leaf = next(v for v in range(n, 0, -1) if v not in has_child)
        target[leaf - 1] = 1
    return edges, target


if __name__ == "__main__":
    E1 = [[2, 4], [1, 2], [6, 8], [1, 3], [5, 7], [2, 5], [3, 6], [6, 10], [6, 9]]
    T1 = [0, 0, 0, 3, 0, 0, 5, 1, 2, 3]
    assert solution(E1, T1) == [1, 1, 2, 2, 2, 3, 3]
    assert solution([[1, 2], [1, 3]], [0, 7, 3]) == [1, 1, 3, 2, 3]
    assert solution([[1, 3], [1, 2]], [0, 7, 1]) == [-1]
    for e, t in (([[1, 2], [1, 3]], [0, 7, 3]), ([[1, 3], [1, 2]], [0, 7, 1])):
        assert solution(e, t) == by_all_sequences(e, t)
    # 6단계 추적: 예시 1에서 숫자가 떨어지는 리프 순서
    children = {1: [2, 3], 2: [4, 5], 3: [6], 5: [7], 6: [8, 9, 10]}
    ptr = {k: 0 for k in children}
    leaves_hit = []
    for _ in range(7):
        v = 1
        while v in children:
            nxt = children[v][ptr[v]]
            ptr[v] = (ptr[v] + 1) % len(children[v])
            v = nxt
        leaves_hit.append(v)
    assert leaves_hit == [4, 8, 7, 9, 4, 10, 7]
    rng = random.Random(150364)
    tested = 0
    while tested < 600:
        n = rng.randint(2, 7)
        e, t = random_case(rng, n)
        if sum(t) > 7:
            continue
        assert solution(e, t) == by_all_sequences(e, t), (e, t)
        tested += 1
    # 노드 101개, 리프 target 최대 100
    e, t = [], None
    n = 101
    e = [[random.Random(2).randint(1, v - 1), v] for v in range(2, n + 1)]
    has_child = {p for p, _ in e}
    t = [random.Random(v).randint(1, 100) if v not in has_child else 0 for v in range(1, n + 1)]
    res = solution(e, t)
    assert res == [-1] or all(x in (1, 2, 3) for x in res)
    print("ALL CHECKS PASSED")
