"""16.완전탐색 문서의 주장을 확인한다."""
from itertools import combinations, permutations, product
from math import comb, factorial, gcd


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    pairs = [p for p in combinations([1, 2, 3, 4], 2) if sum(p) == 5]
    check(pairs == [(1, 4), (2, 3)] and comb(4, 2) == 6, "예시")
    check(comb(1000, 2) == 499500, "1000장에서 두 장")
    for n in range(0, 9):
        a = list(range(n))
        check(len(list(permutations(a))) == factorial(n), "n!")
        check(len(list(product([0, 1], repeat=n))) == 2 ** n, "2^n")
        for r in range(n + 1):
            check(len(list(permutations(a, r))) == factorial(n) // factorial(n - r), "순열")
            check(len(list(combinations(a, r))) == comb(n, r), "조합")
        check(sum(comb(n, r) for r in range(n + 1)) == 2 ** n, "부분집합")
    check(factorial(10) == 3628800 and comb(10, 3) == 120 and factorial(10) // factorial(7) == 720, "n=10 칸")
    check(list(product([0, 1], repeat=2)) == [(0, 0), (0, 1), (1, 0), (1, 1)], "product 예")
    check(list(permutations("abc", 2)) == [("a", "b"), ("a", "c"), ("b", "a"), ("b", "c"), ("c", "a"), ("c", "b")], "permutations 예")
    check(list(combinations("abc", 2)) == [("a", "b"), ("a", "c"), ("b", "c")], "combinations 예")
    # 주기 p, q인 두 상태를 합친 것은 lcm(p, q)마다 되풀이되고, 그보다 짧은 전체 주기는 없다
    for p in range(1, 21):
        for q in range(1, 21):
            L = p * q // gcd(p, q)
            state = [(t % p, t % q) for t in range(2 * L)]
            check(all(state[t] == state[t + L] for t in range(L)), "lcm마다 되풀이")
            check(all(state[d] != state[0] for d in range(1, L)), "더 짧은 주기 없음")
    # 확인 문제
    check(len(list(permutations(range(5), 3))) == 60, "C1")
    check(comb(6, 2) == 15 and factorial(6) == 720 and 10 ** 4 == 10000, "C2")
    check(5 * 6 // gcd(5, 6) == 30, "C3")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
