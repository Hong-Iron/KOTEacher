"""양과 늑대 (프로그래머스 92343) 풀이와 검증."""
import random


def solution(info, edges):
    n = len(info)
    parent = [-1] * n
    for p, c in edges:
        parent[c] = p
    best = 0
    seen = set()

    def go(mask, sheep, wolf):
        nonlocal best
        if mask in seen:
            return
        seen.add(mask)
        best = max(best, sheep)
        for v in range(n):
            if not (mask >> v) & 1 and (mask >> parent[v]) & 1:
                s = sheep + (info[v] == 0)
                w = wolf + (info[v] == 1)
                if s > w:
                    go(mask | (1 << v), s, w)

    go(1, 1, 0)
    return best


def naive(info, edges, counter=None):
    ch = [[] for _ in info]
    for p, c in edges:
        ch[p].append(c)
    best = 0

    def go(s, w, nexts):
        nonlocal best
        if counter is not None:
            counter[0] += 1
        best = max(best, s)
        for node in nexts:
            s2, w2 = s + (info[node] == 0), w + (info[node] == 1)
            if w2 >= s2:
                continue
            go(s2, w2, [x for x in nexts if x != node] + ch[node])

    go(1, 0, ch[0])
    return best


def rand_tree(rng, n):
    edges, kids = [], [0] * n
    for c in range(1, n):
        p = rng.choice([x for x in range(c) if kids[x] < 2])
        kids[p] += 1
        edges.append([p, c])
    info = [0] + [rng.randint(0, 1) for _ in range(n - 1)]
    return info, edges


if __name__ == "__main__":
    assert solution([0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1],
                    [[0, 1], [1, 2], [1, 4], [0, 8], [8, 7], [9, 10], [9, 11], [4, 3], [6, 5], [4, 6], [8, 9]]) == 5
    assert solution([0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0],
                    [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [2, 6], [3, 7], [4, 8], [6, 9], [9, 10]]) == 5
    assert solution([0, 1, 0, 0], [[0, 1], [0, 2], [1, 3]]) == 3
    rng = random.Random(92343)
    for _ in range(400):
        info, edges = rand_tree(rng, rng.randint(2, 8))
        assert solution(info, edges) == naive(info, edges), (info, edges)
    # 별 모양 트리: 기억 없는 재귀의 호출 수
    for k, want in ((8, 109601), (9, 986410)):
        cnt = [0]
        naive([0] * (k + 1), [[0, i] for i in range(1, k + 1)], cnt)
        assert cnt[0] == want, cnt
    # 노드 17개(최대) 별 모양도 기억 방식은 금방 끝난다
    assert solution([0] * 17, [[0, i] for i in range(1, 17)]) == 17
    print("ALL CHECKS PASSED")
