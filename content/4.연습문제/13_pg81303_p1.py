"""표 편집 (프로그래머스 81303) 풀이와 검증."""
import bisect
import random
import time


def solution(n, k, cmd):
    prev = [i - 1 for i in range(n)]
    nxt = [i + 1 for i in range(n)]
    removed = []
    cur = k
    for c in cmd:
        if c[0] == "U":
            for _ in range(int(c[2:])):
                cur = prev[cur]
        elif c[0] == "D":
            for _ in range(int(c[2:])):
                cur = nxt[cur]
        elif c[0] == "C":
            removed.append(cur)
            p, q = prev[cur], nxt[cur]
            if p != -1:
                nxt[p] = q
            if q != n:
                prev[q] = p
            cur = q if q != n else p          # 마지막 행이면 위로
        else:                                 # Z
            x = removed.pop()
            p, q = prev[x], nxt[x]
            if p != -1:
                nxt[p] = x
            if q != n:
                prev[q] = x
    ans = ["O"] * n
    for x in removed:
        ans[x] = "X"
    return "".join(ans)


def by_list(n, k, cmd, log=None):
    """살아 있는 행 번호를 리스트로 들고 문제 그대로 흉내 낸다."""
    table, stack, cur = list(range(n)), [], k      # cur은 선택된 행의 원래 번호
    for c in cmd:
        i = table.index(cur)
        if c[0] == "U":
            cur = table[i - int(c[2:])]
        elif c[0] == "D":
            cur = table[i + int(c[2:])]
        elif c[0] == "C":
            stack.append(table.pop(i))
            cur = table[i] if i < len(table) else table[i - 1]
        else:
            bisect.insort(table, stack.pop())
        if log is not None:
            log.append((c, cur, "".join("O" if r in table else "X" for r in range(n)), list(stack)))
    return "".join("O" if r in set(table) else "X" for r in range(n))


if __name__ == "__main__":
    c1 = ["D 2", "C", "U 3", "C", "D 4", "C", "U 2", "Z", "Z"]
    assert solution(8, 2, c1) == "OOOOXOOO"
    assert solution(8, 2, c1 + ["U 1", "C"]) == "OOXOXOOO"
    # 1단계 예
    l1 = []
    assert solution(5, 2, ["C", "C", "Z"]) == by_list(5, 2, ["C", "C", "Z"], l1) == "OOXOO"
    assert [cur for _, cur, _, _ in l1] == [3, 4, 4]
    # 6단계 추적
    log = []
    by_list(8, 2, c1, log)
    assert log == [
        ("D 2", 4, "OOOOOOOO", []),
        ("C", 5, "OOOOXOOO", [4]),
        ("U 3", 1, "OOOOXOOO", [4]),
        ("C", 2, "OXOOXOOO", [4, 1]),
        ("D 4", 7, "OXOOXOOO", [4, 1]),
        ("C", 6, "OXOOXOOX", [4, 1, 7]),
        ("U 2", 3, "OXOOXOOX", [4, 1, 7]),
        ("Z", 3, "OXOOXOOO", [4, 1]),
        ("Z", 3, "OOOOXOOO", [4]),
    ], log
    # 무작위 비교
    rng = random.Random(81303)
    for _ in range(3000):
        n = rng.randint(5, 12)
        k = rng.randrange(n)
        table, stack, cur, cmd = list(range(n)), [], k, []
        for _ in range(rng.randint(1, 25)):
            i = table.index(cur)
            r = rng.random()
            if r < 0.25 and i > 0:
                x = rng.randint(1, i); cmd.append(f"U {x}"); cur = table[i - x]
            elif r < 0.5 and i < len(table) - 1:
                x = rng.randint(1, len(table) - 1 - i); cmd.append(f"D {x}"); cur = table[i + x]
            elif r < 0.8 and len(table) > 1:
                cmd.append("C"); stack.append(table.pop(i))
                cur = table[i] if i < len(table) else table[i - 1]
            elif stack:
                cmd.append("Z"); bisect.insort(table, stack.pop())
        assert solution(n, k, cmd) == by_list(n, k, cmd), (n, k, cmd)
    # 효율성: 행 100만 개, 명령 20만 개(삭제·복구 위주, 이동 합 100만)
    n = 1_000_000
    big = []
    for i in range(200_000):
        big.append("C" if i % 4 < 2 else ("Z" if i % 4 == 2 else "D 5"))
    t0 = time.perf_counter()
    solution(n, n // 2, big)
    t = time.perf_counter() - t0
    assert t < 5, t
    print(f"n=1e6, cmd=2e5: {t:.2f}s")
    print("ALL CHECKS PASSED")
