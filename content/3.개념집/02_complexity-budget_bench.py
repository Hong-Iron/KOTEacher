"""02.시간 복잡도로 방법 고르기: 이 컴퓨터에서 파이썬의 속도를 잰다.

재는 것
1. 단순 반복(더하기)을 1초에 몇 번 하는가.
2. 리스트에서 `in`(O(n))과 집합에서 `in`(평균 O(1))의 차이.
3. 원소 100만 개 정렬(O(n log n))에 걸리는 시간.
4. n을 두 배로 늘렸을 때 O(n^2) 코드의 시간이 약 네 배가 되는지(로그-로그 기울기).
측정값은 컴퓨터마다 다르므로, 확인하는 것은 크기의 차수와 비율뿐이다.
"""
import math
import random
import time


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def timed(f, *a):
    t = time.perf_counter()
    f(*a)
    return time.perf_counter() - t


def loop(n):
    s = 0
    for i in range(n):
        s += i
    return s


def pairs(n):
    c = 0
    for i in range(n):
        for j in range(n):
            c += 1
    return c


def main():
    n = 5 * 10**6
    t = timed(loop, n)
    ops = n / t
    print(f"단순 반복: 1초에 약 {ops:,.0f}번")
    check(10**6 <= ops <= 10**9, "반복 속도가 상식 범위 밖")

    data = list(range(20000))
    s = set(data)
    qs = [random.randrange(40000) for _ in range(2000)]
    t_list = timed(lambda: [q in data for q in qs])
    t_set = timed(lambda: [q in s for q in qs])
    print(f"리스트 in 2000번: {t_list:.4f}초, 집합 in 2000번: {t_set:.6f}초, 비율 {t_list / t_set:.0f}배")
    check(t_list > 20 * t_set, "집합 in이 리스트 in보다 훨씬 빨라야 한다")

    arr = [random.random() for _ in range(10**6)]
    t_sort = timed(sorted, arr)
    print(f"실수 100만 개 정렬: {t_sort:.3f}초")
    check(t_sort < 5, "정렬이 너무 느리다")

    # O(n^2)의 로그-로그 기울기
    ns = [300, 600, 1200]
    ts = [min(timed(pairs, k) for _ in range(3)) for k in ns]
    slope = (math.log(ts[-1]) - math.log(ts[0])) / (math.log(ns[-1]) - math.log(ns[0]))
    print(f"이중 반복 시간: {[round(x, 4) for x in ts]}, 기울기 {slope:.2f}")
    check(1.7 <= slope <= 2.3, "O(n^2)의 기울기는 약 2")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
