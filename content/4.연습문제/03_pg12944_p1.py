"""평균 구하기 (프로그래머스 12944) 풀이와 검증."""
import random
from fractions import Fraction


def solution(arr):
    return sum(arr) / len(arr)


def solution_loop(arr):
    total = 0
    for x in arr:
        total += x
    return total / len(arr)


if __name__ == "__main__":
    assert solution([1, 2, 3, 4]) == 2.5
    assert solution([5, 5]) == 5
    assert solution([2, 4, 9]) == 5 and solution([1, 2]) == 1.5 and solution([-3, 3]) == 0
    rng = random.Random(12944)
    for _ in range(1000):
        arr = [rng.randint(-10000, 10000) for _ in range(rng.randint(1, 100))]
        exact = Fraction(sum(arr), len(arr))
        assert solution(arr) == solution_loop(arr)
        assert abs(Fraction(solution(arr)) - exact) < Fraction(1, 10**9)
    print("ALL CHECKS PASSED")
