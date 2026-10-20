"""동영상 재생기 (프로그래머스 340213) 풀이와 검증."""
import random


def solution(video_len, pos, op_start, op_end, commands):
    def sec(t):
        m, s = map(int, t.split(":"))
        return m * 60 + s

    length, now = sec(video_len), sec(pos)
    start, end = sec(op_start), sec(op_end)

    def skip(x):
        return end if start <= x <= end else x

    now = skip(now)
    for c in commands:
        if c == "prev":
            now = max(0, now - 10)
        else:
            now = min(length, now + 10)
        now = skip(now)
    m, s = divmod(now, 60)
    return f"{m:02d}:{s:02d}"


def stepwise(video_len, pos, op_start, op_end, commands):
    """10초 이동을 1초씩 10번으로 나누고, 경계에 닿으면 멈춘다."""
    def sec(t):
        return int(t[:2]) * 60 + int(t[3:])
    L, p, a, b = sec(video_len), sec(pos), sec(op_start), sec(op_end)
    if a <= p <= b:
        p = b
    for c in commands:
        for _ in range(10):
            if c == "prev" and p > 0:
                p -= 1
            elif c == "next" and p < L:
                p += 1
        if a <= p <= b:
            p = b
    return "%02d:%02d" % (p // 60, p % 60)


def mmss(x):
    return f"{x // 60:02d}:{x % 60:02d}"


if __name__ == "__main__":
    assert solution("34:33", "13:00", "00:55", "02:55", ["next", "prev"]) == "13:00"
    assert solution("10:55", "00:05", "00:15", "06:55", ["prev", "next", "next"]) == "06:55"
    assert solution("07:22", "04:05", "00:15", "04:07", ["next"]) == "04:17"
    assert solution("10:00", "01:05", "01:00", "02:00", ["next"]) == "02:10"
    rng = random.Random(340213)
    for _ in range(3000):
        L = rng.randint(1, 59 * 60 + 59)
        p = rng.randint(0, L)
        a = rng.randint(0, L - 1) if L > 0 else 0
        b = rng.randint(a + 1, L)
        cmds = [rng.choice(["prev", "next"]) for _ in range(rng.randint(1, 20))]
        args = (mmss(L), mmss(p), mmss(a), mmss(b), cmds)
        assert solution(*args) == stepwise(*args), args
    print("ALL CHECKS PASSED")
