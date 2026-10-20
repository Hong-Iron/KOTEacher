"""같은 숫자는 싫어 (프로그래머스 12906) 풀이와 검증."""
import random
from itertools import groupby


def solution(arr):
    answer = []
    for x in arr:
        if not answer or answer[-1] != x:
            answer.append(x)
    return answer


def by_groupby(arr):
    return [k for k, _ in groupby(arr)]


def buggy(arr):
    """7단계의 흔한 실수: arr[i - 1]과 비교 (i = 0에서 끝 원소와 비교한다)."""
    return [arr[i] for i in range(len(arr)) if arr[i] != arr[i - 1]]


if __name__ == "__main__":
    assert solution([1, 1, 3, 3, 0, 1, 1]) == [1, 3, 0, 1]
    assert solution([4, 4, 4, 3, 3]) == [4, 3]
    assert solution([4, 4, 1, 1, 1, 4]) == [4, 1, 4]
    assert buggy([4, 4, 1, 1, 1, 4]) == [1, 4]      # 첫 4를 빼먹는다
    rng = random.Random(12906)
    for _ in range(2000):
        arr = [rng.randint(0, 9) for _ in range(rng.randint(1, 40))]
        assert solution(arr) == by_groupby(arr)
    print("ALL CHECKS PASSED")
