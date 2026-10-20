"""매출 하락 최소화 (프로그래머스 72416) 풀이와 검증."""
import random
import time
from itertools import combinations


def solution(sales, links, table=None):
    n = len(sales)
    children = [[] for _ in range(n + 1)]
    for a, b in links:
        children[a].append(b)
    order, stack = [], [1]
    while stack:                               # 뿌리부터 내려가는 순서
        v = stack.pop()
        order.append(v)
        stack.extend(children[v])
    go = [0] * (n + 1)                         # go[v]: v가 간다
    stay = [0] * (n + 1)                       # stay[v]: v가 안 간다
    for v in reversed(order):                  # 자식이 먼저
        base = sum(min(go[c], stay[c]) for c in children[v])
        go[v] = sales[v - 1] + base
        if not children[v]:
            stay[v] = 0                        # 팀장이 아니면 v 때문에 채울 팀이 없다
        elif any(go[c] <= stay[c] for c in children[v]):
            stay[v] = base                     # 팀원 중 누군가 이미 가는 편이 싸다
        else:
            stay[v] = base + min(go[c] - stay[c] for c in children[v])   # 한 명은 억지로 보낸다
        if table is not None:
            table[v] = (go[v], stay[v])
    return min(go[1], stay[1])


def by_subsets(sales, links):
    n = len(sales)
    teams = {}
    for a, b in links:
        teams.setdefault(a, {a}).add(b)
    best = None
    for k in range(n + 1):
        for comb in combinations(range(1, n + 1), k):
            s = set(comb)
            if all(team & s for team in teams.values()):
                cost = sum(sales[v - 1] for v in comb)
                best = cost if best is None else min(best, cost)
    return best


if __name__ == "__main__":
    ex = ([14, 17, 15, 18, 19, 14, 13, 16, 28, 17],
          [[10, 8], [1, 9], [9, 7], [5, 4], [1, 5], [5, 10], [10, 6], [1, 3], [10, 2]])
    assert solution(*ex) == 44 == by_subsets(*ex)
    assert solution([5, 6, 5, 3, 4], [[2, 3], [1, 4], [2, 5], [1, 2]]) == 6
    assert solution([5, 6, 5, 1, 4], [[2, 3], [1, 4], [2, 5], [1, 2]]) == 5
    assert solution([10, 10, 1, 1], [[3, 2], [4, 3], [1, 4]]) == 2
    # 6단계 추적: 예시 1의 (간다, 안 간다)
    tb = {}
    solution(*ex, table=tb)
    assert tb[10] == (17, 14) and tb[5] == (33, 17) and tb[9] == (28, 13) and tb[1] == (44, 45)
    assert tb[7] == (13, 0) and tb[3] == (15, 0)
    rng = random.Random(72416)
    for _ in range(1500):
        n = rng.randint(2, 10)
        links = [[rng.randint(1, v - 1), v] for v in range(2, n + 1)]
        sales = [rng.randint(0, 20) for _ in range(n)]
        assert solution(sales, links) == by_subsets(sales, links), (sales, links)
    # 30만 명, 한 줄로 이어진 조직도
    n = 300_000
    links = [[v - 1, v] for v in range(2, n + 1)]
    sales = [rng.randint(0, 10_000) for _ in range(n)]
    t0 = time.perf_counter()
    solution(sales, links)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"300k chain: {t:.2f}s")
    print("ALL CHECKS PASSED")
