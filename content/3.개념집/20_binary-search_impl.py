"""20.이분 탐색: lower bound를 구현하고 문서의 주장을 확인한다."""
import math
import random
from bisect import bisect_left, bisect_right


def lower_bound(a, x, steps=None):
    lo, hi = 0, len(a)
    while lo < hi:
        if steps is not None:
            steps.append((lo, hi, (lo + hi) // 2))
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_like(a, x):
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def bad_lower(a, x, limit=100):
    """lo = mid로 쓴 틀린 버전. limit번 넘게 돌면 None."""
    lo, hi = 0, len(a)
    for _ in range(limit):
        if lo >= hi:
            return lo
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid
        else:
            hi = mid
    return None


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    a = [2, 4, 4, 7, 9, 12, 15, 20]
    st = []
    check(lower_bound(a, 7, st) == 3 and st == [(0, 8, 4), (0, 4, 2), (3, 4, 3)], "예시 표")
    check(lower_bound(a, 6) == 3, "6 이상인 첫 위치")
    rng = random.Random(20)
    for _ in range(5000):
        n = rng.randint(0, 40)
        arr = sorted(rng.randint(0, 15) for _ in range(n))
        x = rng.randint(-2, 17)
        st = []
        got = lower_bound(arr, x, st)
        check(got == bisect_left(arr, x) == sum(1 for v in arr if v < x), (arr, x))
        check(len(st) <= math.ceil(math.log2(n + 1)), "반복 횟수")
        check(upper_like(arr, x) == bisect_right(arr, x) == sum(1 for v in arr if v <= x), "C2")
        L, R = sorted((rng.randint(0, 15), rng.randint(0, 15)))
        check(bisect_right(arr, R) - bisect_left(arr, L) == sum(1 for v in arr if L <= v <= R), "구간 개수")
        check(len(arr) - bisect_left(arr, x) == sum(1 for v in arr if v >= x), "x 이상 개수")
        check(bisect_right(arr, x) - bisect_left(arr, x) == arr.count(x), "x의 개수")
    # C1
    b = [1, 3, 3, 3, 8]
    check(bisect_left(b, 3) == 1 and bisect_right(b, 3) == 4, "C1")
    # C4: 정렬 안 된 리스트
    check(bisect_left([5, 1, 3], 5) == 3 and lower_bound([5, 1, 3], 5) == 3, "C4 (정답은 0)")
    # 오해: lo = mid는 끝나지 않는다
    check(bad_lower([1, 3], 3) is None, "lo = mid 무한 반복")
    check(math.ceil(math.log2(10**6 + 1)) == 20, "100만에서 20번")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
