"""n진수 게임 (프로그래머스 17687) 풀이와 검증."""
import random


def solution(n, t, m, p):
    digits = "0123456789ABCDEF"

    def to_base(x):
        if x == 0:
            return "0"
        s = ""
        while x > 0:
            x, r = divmod(x, n)
            s = digits[r] + s
        return s

    parts, length, num = [], 0, 0
    while length < t * m:
        part = to_base(num)
        parts.append(part)
        length += len(part)
        num += 1
    seq = "".join(parts)
    return seq[p - 1::m][:t]


def game(n, t, m, p):
    """사람을 한 명씩 돌리며, 말할 숫자를 한 글자씩 넘긴다."""
    digits = "0123456789ABCDEF"

    def conv(x):
        return "0" if x == 0 else conv_rec(x)

    def conv_rec(x):
        return "" if x == 0 else conv_rec(x // n) + digits[x % n]

    said, num, buf, turn = [], 0, "", 1
    while len(said) < t:
        if not buf:
            buf = conv(num)
            num += 1
        ch, buf = buf[0], buf[1:]
        if turn == p:
            said.append(ch)
        turn = turn % m + 1
    return "".join(said)


if __name__ == "__main__":
    assert solution(2, 4, 2, 1) == "0111"
    assert solution(16, 16, 2, 1) == "02468ACE11111111"
    assert solution(16, 16, 2, 2) == "13579BDF01234567"
    assert solution(10, 3, 3, 2) == "147"
    rng = random.Random(17687)
    for _ in range(2000):
        n, m = rng.randint(2, 16), rng.randint(2, 10)
        p, t = rng.randint(1, m), rng.randint(1, 60)
        assert solution(n, t, m, p) == game(n, t, m, p), (n, t, m, p)
    # 2·8·16진수 전체 줄을 format과 비교 (m=1, p=1이면 전체 줄 앞부분이 그대로 나온다)
    for base, fmt in ((2, "b"), (8, "o"), (16, "X")):
        want = "".join(format(x, fmt) for x in range(300))
        assert solution(base, len(want), 1, 1) == want[:len(want)]
    print("ALL CHECKS PASSED")
