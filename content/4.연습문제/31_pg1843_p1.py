"""사칙연산 (프로그래머스 1843) 풀이와 검증."""
import random
import time
from functools import lru_cache


def solution(arr):
    nums = [int(x) for x in arr[0::2]]
    ops = arr[1::2]                            # ops[k]: nums[k]와 nums[k+1] 사이 연산자
    n = len(nums)
    INF = float("inf")
    mx = [[-INF] * n for _ in range(n)]        # mx[i][j]: nums[i..j] 식의 최댓값
    mn = [[INF] * n for _ in range(n)]         # mn[i][j]: 최솟값
    for i in range(n):
        mx[i][i] = mn[i][i] = nums[i]
    for length in range(2, n + 1):             # 짧은 구간부터
        for i in range(n - length + 1):
            j = i + length - 1
            for k in range(i, j):              # 마지막으로 계산하는 연산자 ops[k]
                if ops[k] == "+":
                    hi = mx[i][k] + mx[k + 1][j]
                    lo = mn[i][k] + mn[k + 1][j]
                else:                          # 빼기: 큰 값 - 작은 값이 가장 크다
                    hi = mx[i][k] - mn[k + 1][j]
                    lo = mn[i][k] - mx[k + 1][j]
                if hi > mx[i][j]:
                    mx[i][j] = hi
                if lo < mn[i][j]:
                    mn[i][j] = lo
    return mx[0][n - 1]


def by_all_orders(arr):
    nums = [int(x) for x in arr[0::2]]
    ops = arr[1::2]

    @lru_cache(maxsize=None)
    def values(i, j):
        if i == j:
            return frozenset([nums[i]])
        out = set()
        for k in range(i, j):
            for a in values(i, k):
                for b in values(k + 1, j):
                    out.add(a + b if ops[k] == "+" else a - b)
        return frozenset(out)

    return max(values(0, len(nums) - 1))


if __name__ == "__main__":
    assert solution(["1", "-", "3", "+", "5", "-", "8"]) == 1
    assert solution(["5", "-", "3", "+", "1", "+", "2", "-", "4"]) == 3
    # 예시 1의 가능한 값 5가지
    ex = ["1", "-", "3", "+", "5", "-", "8"]
    nums, ops = [1, 3, 5, 8], ["-", "+", "-"]

    @lru_cache(maxsize=None)
    def vals(i, j):
        if i == j:
            return (nums[i],)
        out = []
        for k in range(i, j):
            for a in vals(i, k):
                for b in vals(k + 1, j):
                    out.append(a + b if ops[k] == "+" else a - b)
        return tuple(out)
    assert sorted(vals(0, 3)) == [-15, -5, -5, 1, 1]
    # 6단계 추적: 구간별 최대·최소
    def table(arr):
        nums = [int(x) for x in arr[0::2]]
        ops = arr[1::2]
        n = len(nums)
        INF = float("inf")
        mx = [[-INF] * n for _ in range(n)]
        mn = [[INF] * n for _ in range(n)]
        for i in range(n):
            mx[i][i] = mn[i][i] = nums[i]
        for length in range(2, n + 1):
            for i in range(n - length + 1):
                j = i + length - 1
                for k in range(i, j):
                    if ops[k] == "+":
                        hi, lo = mx[i][k] + mx[k + 1][j], mn[i][k] + mn[k + 1][j]
                    else:
                        hi, lo = mx[i][k] - mn[k + 1][j], mn[i][k] - mx[k + 1][j]
                    mx[i][j], mn[i][j] = max(mx[i][j], hi), min(mn[i][j], lo)
        return mx, mn
    mx, mn = table(ex)
    assert [(mx[i][i + 1], mn[i][i + 1]) for i in range(3)] == [(-2, -2), (8, 8), (-3, -3)]
    assert (mx[1][3], mn[1][3]) == (0, 0) and (mx[0][2], mn[0][2]) == (3, -7) and (mx[0][3], mn[0][3]) == (1, -15)
    # 최댓값만 들고 다니면 틀린다: 빼기 뒤쪽은 최소가 필요하다
    def max_only(arr):
        nums = [int(x) for x in arr[0::2]]
        ops = arr[1::2]
        n = len(nums)
        mx = [[None] * n for _ in range(n)]
        for i in range(n):
            mx[i][i] = nums[i]
        for length in range(2, n + 1):
            for i in range(n - length + 1):
                j = i + length - 1
                mx[i][j] = max((mx[i][k] + mx[k + 1][j]) if ops[k] == "+" else (mx[i][k] - mx[k + 1][j])
                               for k in range(i, j))
        return mx[0][n - 1]
    ones = ["1", "-", "1", "-", "1", "-", "1"]
    assert max_only(ones) == 0 and solution(ones) == 2 == 1 - ((1 - 1) - 1)
    rng = random.Random(1843)
    for _ in range(2000):
        k = rng.randint(2, 7)
        arr = []
        for i in range(k):
            arr.append(str(rng.randint(1, 20)))
            if i < k - 1:
                arr.append(rng.choice("+-"))
        assert solution(arr) == by_all_orders(arr), arr
    arr = []
    for i in range(101):
        arr.append(str(rng.randint(1, 1000)))
        if i < 100:
            arr.append(rng.choice("+-"))
    t0 = time.perf_counter()
    solution(arr)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"101 numbers: {t:.2f}s")
    print("ALL CHECKS PASSED")
