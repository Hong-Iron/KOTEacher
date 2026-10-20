"""k진수에서 소수 개수 구하기 (프로그래머스 92335) 풀이와 검증."""
import random


def is_prime(x):
    if x < 2:
        return False
    i = 2
    while i * i <= x:
        if x % i == 0:
            return False
        i += 1
    return True


def solution(n, k):
    digits = ""
    while n > 0:
        n, r = divmod(n, k)
        digits = str(r) + digits
    return sum(1 for part in digits.split("0") if part and is_prime(int(part)))


def to_base(n, k):
    return "" if n == 0 else to_base(n // k, k) + str(n % k)


def slow(n, k):
    """모든 구간 [i, j)에서 P가 0 없는 덩어리이고 양옆이 0이거나 끝인 것을 센다."""
    s = to_base(n, k)
    L, cnt = len(s), 0
    for i in range(L):
        for j in range(i + 1, L + 1):
            p = s[i:j]
            if "0" in p:
                continue
            left_ok = i == 0 or s[i - 1] == "0"
            right_ok = j == L or s[j] == "0"
            if left_ok and right_ok:
                x = int(p)
                if x >= 2 and all(x % d for d in range(2, int(x ** 0.5) + 1)):
                    cnt += 1
    return cnt


if __name__ == "__main__":
    assert to_base(437674, 3) == "211020101011" and to_base(77, 4) == "1031"
    assert solution(437674, 3) == 3
    assert solution(110011, 10) == 2
    assert solution(77, 4) == 1
    # 소수 판정을 체와 비교
    N = 100000
    sieve = [False, False] + [True] * (N - 1)
    for i in range(2, int(N ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, N + 1, i):
                sieve[j] = False
    assert all(is_prime(x) == sieve[x] for x in range(N + 1))
    rng = random.Random(92335)
    for _ in range(2000):
        n, k = rng.randint(1, 1_000_000), rng.randint(3, 10)
        assert solution(n, k) == slow(n, k), (n, k)
    print("ALL CHECKS PASSED")
