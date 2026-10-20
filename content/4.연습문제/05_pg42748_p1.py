"""K번째수 (프로그래머스 42748) 풀이와 검증."""
import random


def solution(array, commands):
    answer = []
    for i, j, k in commands:
        part = sorted(array[i - 1:j])
        answer.append(part[k - 1])
    return answer


def brute(array, commands):
    """정렬 없이: 구간 안에서 '자기보다 작은 수 < k <= 자기 이하 수'인 값을 찾는다."""
    out = []
    for i, j, k in commands:
        part = array[i - 1:j]
        for v in part:
            less = sum(1 for x in part if x < v)
            leq = sum(1 for x in part if x <= v)
            if less < k <= leq:
                out.append(v)
                break
    return out


if __name__ == "__main__":
    assert solution([1, 5, 2, 6, 3, 7, 4], [[2, 5, 3], [4, 4, 1], [1, 7, 3]]) == [5, 6, 3]
    assert solution([9, 4, 7, 1], [[1, 3, 2]]) == [7]
    rng = random.Random(42748)
    for _ in range(1000):
        n = rng.randint(1, 100)
        array = [rng.randint(1, 100) for _ in range(n)]
        commands = []
        for _ in range(rng.randint(1, 50)):
            i = rng.randint(1, n)
            j = rng.randint(i, n)
            commands.append([i, j, rng.randint(1, j - i + 1)])
        before = array[:]
        assert solution(array, commands) == brute(array, commands)
        assert array == before
    print("ALL CHECKS PASSED")
