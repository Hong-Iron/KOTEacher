"""17.재귀와 백트래킹 문서와 예제 사다리의 주장을 확인한다."""
import random
import sys
from itertools import combinations, permutations


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def total(n):
    if n == 0:
        return 0
    return total(n - 1) + n


def perms(items, k):
    out, chosen, used = [], [], set()

    def go():
        if len(chosen) == k:
            out.append(tuple(chosen))
            return
        for x in items:
            if x in used:
                continue
            chosen.append(x); used.add(x)
            go()
            chosen.pop(); used.discard(x)
    go()
    return out


def count_subsets(nums, target, counter=None):
    nums = sorted(nums)

    def go(start, remain):
        if counter is not None:
            counter[0] += 1
        if remain == 0:
            return 1
        cnt = 0
        for i in range(start, len(nums)):
            if nums[i] > remain:
                break
            cnt += go(i + 1, remain - nums[i])
        return cnt
    return go(0, target)


def count_no_prune(nums, target, counter):
    def go(i, remain):
        counter[0] += 1
        if i == len(nums):
            return 1 if remain == 0 else 0
        return go(i + 1, remain) + go(i + 1, remain - nums[i])
    return go(0, target)


def brute_subsets(nums, target):
    return sum(1 for r in range(1, len(nums) + 1) for c in combinations(nums, r) if sum(c) == target)


def n_queens(n):
    cols, d1, d2 = set(), set(), set()

    def go(r):
        if r == n:
            return 1
        s = 0
        for c in range(n):
            if c in cols or r - c in d1 or r + c in d2:
                continue
            cols.add(c); d1.add(r - c); d2.add(r + c)
            s += go(r + 1)
            cols.discard(c); d1.discard(r - c); d2.discard(r + c)
        return s
    return go(0)


def parens(n):
    out = []

    def go(s, opened, closed):
        if len(s) == 2 * n:
            out.append(s)
            return
        if opened < n:
            go(s + "(", opened + 1, closed)
        if closed < opened:
            go(s + ")", opened, closed + 1)
    go("", 0, 0)
    return out


def combos(n, k):
    out, chosen = [], []

    def go(start):
        if len(chosen) == k:
            out.append(tuple(chosen))
            return
        for x in range(start, n + 1):
            chosen.append(x)
            go(x + 1)
            chosen.pop()
    go(1)
    return out


def main():
    check(all(total(n) == n * (n + 1) // 2 for n in range(501)), "total")
    check(perms([1, 2, 3], 2) == list(permutations([1, 2, 3], 2)), "두 자리 순서")
    rng = random.Random(17)
    for _ in range(2000):
        nums = [rng.randint(1, 9) for _ in range(rng.randint(0, 9))]
        t = rng.randint(1, 20)
        check(count_subsets(nums, t) == brute_subsets(nums, t), (nums, t))
    a, b = [0], [0]
    nums = list(range(1, 16))
    check(count_subsets(nums, 20, a) == count_no_prune(nums, 20, b), "가지치기와 결과 같음")
    print(f"방문 수: 가지치기 {a[0]}, 없이 {b[0]}")
    check(a[0] < b[0] // 10, "가지치기로 방문이 크게 줄어야 한다")
    # 가정이 깨지는 예
    check(count_subsets([-3, -2], -5) == 0 and brute_subsets([-3, -2], -5) == 1, "음수 반례")
    # 재귀 한도
    check(sys.getrecursionlimit() == 1000, "기본 한도")

    def deep(n):
        return 0 if n == 0 else deep(n - 1) + 1
    try:
        deep(5000)
        check(False, "RecursionError가 나야 한다")
    except RecursionError:
        pass
    # C1: 값 5, 호출 9번
    calls = [0]

    def f(n):
        calls[0] += 1
        return 1 if n <= 1 else f(n - 1) + f(n - 2)
    check(f(4) == 5 and calls[0] == 9, "C1")
    # 오해: 되돌리기를 빼면 틀린다
    out, chosen = [], []

    def bad():
        if len(chosen) >= 2 and len(out) < 6:
            out.append(tuple(chosen))
            return
        if len(out) >= 6:
            return
        for x in [1, 2, 3]:
            if x in chosen:
                continue
            chosen.append(x)
            bad()
    bad()
    check(out != list(permutations([1, 2, 3], 2)), "되돌리기 없으면 다르다")
    # 예제 사다리
    check(combos(4, 2) == list(combinations(range(1, 5), 2)) and len(combos(5, 3)) == 10, "사다리 1")
    check(count_subsets([2, 3, 5, 7], 10) == 2, "사다리 2")
    check([n_queens(n) for n in range(1, 9)] == [1, 0, 0, 2, 10, 4, 40, 92], "사다리 3")
    p3 = parens(3)
    check(p3 == ["((()))", "(()())", "(())()", "()(())", "()()()"] and len(parens(4)) == 14, "사다리 4")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
