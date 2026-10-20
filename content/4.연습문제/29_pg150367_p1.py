"""표현 가능한 이진트리 (프로그래머스 150367) 풀이와 검증."""
import random
import time


def solution(numbers):
    def ok(s):                               # s: 포화 이진 트리를 중위 순서로 늘어놓은 문자열
        if len(s) == 1:
            return True
        mid = len(s) // 2
        if s[mid] == "0":                    # 뿌리가 더미면 아래도 모두 더미여야 한다
            return "1" not in s
        return ok(s[:mid]) and ok(s[mid + 1:])

    answer = []
    for x in numbers:
        b = bin(x)[2:]
        size = 1
        while size < len(b):                 # 1, 3, 7, 15, … 중 길이 이상인 가장 작은 것
            size = size * 2 + 1
        answer.append(1 if ok(b.zfill(size)) else 0)
    return answer


def representable_upto(H):
    """높이 H 이하의 포화 틀에서, 뿌리를 포함하고 부모가 있어야 자식이 있는 모든 나무의 수를 모은다."""
    out = set()
    for h in range(H + 1):
        L = 2 ** (h + 1) - 1

        def subtrees(lo, hi):
            """[lo, hi] 구간(포화 이진 트리)의 뿌리를 포함하는 부분 나무들: 칸 번호 집합의 목록."""
            if lo > hi:
                return [frozenset()]
            m = (lo + hi) // 2
            res = []
            lefts = [frozenset()] + [t for t in subtrees(lo, m - 1) if t]
            rights = [frozenset()] + [t for t in subtrees(m + 1, hi) if t]
            for a in lefts:
                for b in rights:
                    res.append(frozenset({m}) | a | b)
            return res

        for t in subtrees(0, L - 1):
            out.add(int("".join("1" if i in t else "0" for i in range(L)), 2))
    return out


if __name__ == "__main__":
    assert solution([7, 42, 5]) == [1, 1, 0]
    assert solution([63, 111, 95]) == [1, 1, 0]
    # 문서 예시: 58 = "0111010"
    assert bin(58)[2:].zfill(7) == "0111010" and solution([58]) == [1]
    # 6단계 추적: 95 = 1011111 → 뿌리 1, 왼쪽 "101"의 뿌리가 0인데 아래에 1
    assert bin(95)[2:] == "1011111" and "1011111"[3] == "1" and "101"[1] == "0"
    assert bin(42)[2:].zfill(7) == "0101010"
    # 한 단계 이상 큰 틀에 넣으면 가운데(뿌리)가 늘 앞에 채운 0이다
    for x in range(1, 5000):
        b = bin(x)[2:]
        size = 1
        while size < len(b):
            size = size * 2 + 1
        for bigger in (size * 2 + 1, size * 4 + 3):
            assert b.zfill(bigger)[bigger // 2] == "0"
    # 크기 1, 3, 7, 15 틀의 모든 나무를 만들어 1 ~ 2^15-1을 전수 비교
    good = representable_upto(3)
    assert len(good) == 1 + 4 + 25 + 676
    nums = list(range(1, 2 ** 15))
    got = solution(nums)
    assert all(g == (1 if x in good else 0) for x, g in zip(nums, got))
    # 가장 큰 수 10^15 (50비트 → 63칸)와 1만 개의 시간
    assert len(bin(10 ** 15)) - 2 == 50
    rng = random.Random(150367)
    big = [rng.randint(1, 10 ** 15) for _ in range(10_000)]
    t0 = time.perf_counter()
    solution(big)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"10000 numbers: {t:.2f}s")
    print("ALL CHECKS PASSED")
