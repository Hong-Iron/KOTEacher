"""18.투 포인터와 슬라이딩 윈도 문서의 주장을 확인한다."""
import random


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def pair_sum(a, target):
    """정렬된 a에서 합이 target인 두 수(값)를 양 끝에서 좁혀 찾는다. 없으면 None."""
    L, R = 0, len(a) - 1
    while L < R:
        s = a[L] + a[R]
        if s == target:
            return a[L], a[R]
        if s > target:
            R -= 1
        else:
            L += 1
    return None


def count_windows(a, S):
    left, s, cnt = 0, 0, 0
    for right in range(len(a)):
        s += a[right]
        while s > S:
            s -= a[left]
            left += 1
        if s == S:
            cnt += 1
    return cnt


def brute_windows(a, S):
    return sum(1 for i in range(len(a)) for j in range(i + 1, len(a) + 1) if sum(a[i:j]) == S)


def main():
    check(pair_sum([1, 3, 4, 6, 8, 11], 10) == (4, 6), "예시 1")
    check(count_windows([2, 1, 3, 2, 4], 6) == 3 == brute_windows([2, 1, 3, 2, 4], 6), "예시 2")
    rng = random.Random(18)
    for _ in range(3000):
        a = sorted(rng.randint(-20, 20) for _ in range(rng.randint(0, 12)))
        t = rng.randint(-30, 30)
        exists = any(a[i] + a[j] == t for i in range(len(a)) for j in range(i + 1, len(a)))
        got = pair_sum(a, t)
        check((got is not None) == exists and (got is None or sum(got) == t), (a, t))
        b = [rng.randint(1, 9) for _ in range(rng.randint(0, 15))]
        S = rng.randint(1, 25)
        check(count_windows(b, S) == brute_windows(b, S), (b, S))
    check(count_windows([4, -2, 1], 3) == 0 and brute_windows([4, -2, 1], 3) == 1, "음수 반례 (C3)")
    # C1: 찾는 순간의 창
    a, S = [1, 2, 3, 4, 5], 9
    left, s, found = 0, 0, []
    for right in range(len(a)):
        s += a[right]
        while s > S:
            s -= a[left]
            left += 1
        if s == S:
            found.append(a[left:right + 1])
    check(found == [[2, 3, 4], [4, 5]], "C1")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
