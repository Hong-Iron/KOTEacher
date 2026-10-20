"""09.비트 연산과 비트마스크 문서의 주장을 확인한다."""
import itertools


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    check(9 | 30 == 31 and 9 & 30 == 8 and 9 ^ 30 == 23, "예시")
    check(format(9, "05b") == "01001" and format(30, "05b") == "11110", "5자리")
    a, b = 12, 10
    check(a & b == 8 and a | b == 14 and a ^ b == 6 and a << 1 == 24 and a >> 2 == 3 and ~a == -13, "연산 표")
    check(bin(9) == "0b1001" and int("1001", 2) == 9, "변환")
    for x in range(256):
        s = format(x, "08b")[::-1]            # s[k] = k번 자리
        for k in range(8):
            on = s[k] == "1"
            check(((x >> k) & 1) == on and ((x & (1 << k)) != 0) == on, "켜져 있나")
            check(format(x | (1 << k), "08b")[::-1][k] == "1", "켜기")
            check(format(x & ~(1 << k), "08b")[::-1][k] == "0", "끄기")
            check(((x ^ (1 << k)) >> k & 1) == (not on), "뒤집기")
        check(bin(x).count("1") == s.count("1"), "켜진 자리 수")
    for n in range(11):
        items = list(range(n))
        subsets = set()
        for mask in range(1 << n):
            subsets.add(frozenset(items[i] for i in range(n) if (mask >> i) & 1))
        check(len(subsets) == 2 ** n, "부분집합 개수")
        check(subsets == {frozenset(c) for r in range(n + 1) for c in itertools.combinations(items, r)}, "모두 만든다")
    n = 6
    for A in range(1 << n):
        for B in range(1 << n):
            sa = {i for i in range(n) if A >> i & 1}
            sb = {i for i in range(n) if B >> i & 1}
            check(((A & B) == A) == (sa <= sb), "부분집합 판정")
    k = 3
    check((1 << k - 1) == 1 << (k - 1) == 4 and (1 << k) - 1 == 7, "+ -가 시프트보다 먼저")
    x = 2
    check((x & 1 == 0) is True and (x & 1 == 0) == ((x & 1) == 0), "파이썬은 & 가 == 보다 먼저")
    # 확인 문제
    check((5 | 3, 5 & 3, 5 ^ 3, 5 << 2) == (7, 1, 6, 20), "C1")
    items = ["a", "b", "c", "d"]
    check([items[i] for i in range(4) if 0b1011 >> i & 1] == ["a", "b", "d"], "C3 가")
    check((1 << 1) | (1 << 2) == 6, "C3 나")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
