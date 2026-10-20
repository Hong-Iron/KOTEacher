"""올바른 괄호의 갯수 (프로그래머스 12929) 풀이와 검증."""
from math import comb


def solution(n):
    dp = [1] + [0] * n                         # dp[k]: 괄호 k쌍으로 만드는 올바른 문자열 수
    for k in range(1, n + 1):
        for i in range(k):                     # 첫 "(" 와 짝인 ")" 안에 i쌍, 밖(뒤)에 k-1-i쌍
            dp[k] += dp[i] * dp[k - 1 - i]
    return dp[n]


def by_generating(n):
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
    return len(out)


if __name__ == "__main__":
    assert solution(2) == 2 and solution(3) == 5
    assert [solution(k) for k in range(0, 6)] == [1, 1, 2, 5, 14, 42]
    for n in range(1, 11):
        assert solution(n) == by_generating(n) == comb(2 * n, n) // (n + 1)
    assert solution(14) == 2_674_440 == comb(28, 14) // 15
    print("ALL CHECKS PASSED")
