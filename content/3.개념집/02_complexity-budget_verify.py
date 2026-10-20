"""02.시간 복잡도로 방법 고르기 문서와 예제 사다리의 계산을 확인한다."""
import math


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    n = 10**5
    # 예시: log2(10^5) ≈ 17, 정렬 방법 ≈ 200만
    check(round(math.log2(n)) == 17, "log2(10^5)")
    check(1.5e6 <= n * math.log2(n) + n <= 2.5e6, "방법 B 횟수")
    check(n * n == 10**10, "방법 A 횟수")
    # 스스로 설명해 보기의 코드: 작은 입력에서 비교 횟수가 n^2 규모
    def slow(participant, completion):
        ops = 0
        completion = completion[:]
        for p in participant:
            ops += len(completion)      # in이 훑는 양(최악)
            if p in completion:
                completion.remove(p)
            else:
                return p, ops
        return None, ops
    names = [f"p{i}" for i in range(2000)]
    _, ops = slow(names, names[:-1][::-1])
    check(ops > 10**6, "방법 A는 n=2000에서도 100만 번이 넘는다")
    # 예제: 다시 나오는 수 세기 (집합)
    def repeats(a):
        seen, c = set(), 0
        for x in a:
            if x in seen:
                c += 1
            seen.add(x)
        return c
    check(repeats([5]) == 0 and repeats([7] * 10) == 9 and repeats([1, 2, 1, 3, 2]) == 2, "예제 경계")
    # 카드
    check(abs(200_000 * 199_999 / 2 - 2e10) < 1e8, "C1 쌍의 수")
    check(2**20 < 1.1e6 and 2**40 > 1e12, "C3")
    # 사다리
    check(2000 * 1999 // 2 == 1_999_000, "사다리 2")
    check(2**18 * 18 == 4_718_592, "사다리 4 (18)")
    check(3.2e10 <= 2**30 * 30 <= 3.3e10, "사다리 4 (30)")
    check(10**6 * math.log2(10**6) < 2.1e7, "사다리 3 정렬")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
