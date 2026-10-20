"""짝수와 홀수 (프로그래머스 12937) 풀이와 검증."""


def solution(num):
    if num % 2 == 0:
        return "Even"
    return "Odd"


if __name__ == "__main__":
    # 문제의 예시
    assert solution(3) == "Odd"
    assert solution(4) == "Even"
    # 음수와 0을 포함한 모든 작은 정수: 끝 비트로 따로 판정한 결과와 비교
    for n in range(-1000, 1001):
        assert solution(n) == ("Odd" if n & 1 else "Even"), n
    assert solution(0) == "Even" and solution(-3) == "Odd"
    print("ALL CHECKS PASSED")
