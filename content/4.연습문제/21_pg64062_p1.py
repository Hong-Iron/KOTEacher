"""징검다리 건너기 (프로그래머스 64062) 풀이와 검증."""
import random
import time
from collections import deque


def solution(stones, k):
    def ok(m):                               # m번째 친구도 건널 수 있나
        run = 0
        for s in stones:
            if s < m:                        # m-1명이 지나가면 0 이하가 되는 돌
                run += 1
                if run >= k:
                    return False
            else:
                run = 0
        return True

    lo, hi = 1, max(stones)
    while lo < hi:                           # 최대형 틀
        mid = (lo + hi + 1) // 2
        if ok(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def by_window(stones, k):
    """길이 k인 창마다 가장 큰 돌 값을 구해, 그중 가장 작은 값을 돌려준다(덱으로 창 최댓값)."""
    dq, best = deque(), None
    for i, s in enumerate(stones):
        while dq and stones[dq[-1]] <= s:
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
        if i >= k - 1:
            m = stones[dq[0]]
            best = m if best is None else min(best, m)
    return best


def by_walking(stones, k):
    """친구를 한 명씩 실제로 건너게 한다."""
    st = stones[:]
    n, people = len(st), 0
    while True:
        pos, steps = -1, []
        while True:
            nxt = next((j for j in range(pos + 1, n) if st[j] > 0), n)
            if nxt - pos > k:
                return people
            if nxt == n:
                break
            steps.append(nxt)
            pos = nxt
        for j in steps:
            st[j] -= 1
        people += 1


if __name__ == "__main__":
    ex = [2, 4, 5, 3, 2, 1, 4, 2, 5, 1]
    assert solution(ex, 3) == 3
    assert solution([2, 1, 3], 2) == by_walking([2, 1, 3], 2) == 2      # 1단계
    # 6단계 추적
    def longest_run(stones, m):
        best = run = 0
        for s in stones:
            run = run + 1 if s < m else 0
            best = max(best, run)
        return best
    assert [longest_run(ex, m) for m in (3, 4)] == [2, 3]
    assert by_walking(ex, 3) == 3 == by_window(ex, 3)
    # 무작위 비교
    rng = random.Random(64062)
    for _ in range(3000):
        n = rng.randint(1, 10)
        st = [rng.randint(1, 6) for _ in range(n)]
        k = rng.randint(1, n)
        a = solution(st, k)
        assert a == by_walking(st, k) == by_window(st, k), (st, k)
    # 효율성: 돌 20만 개, 값 2억까지
    big = [rng.randint(1, 200_000_000) for _ in range(200_000)]
    t0 = time.perf_counter()
    r = solution(big, 1000)
    tt = time.perf_counter() - t0
    assert r == by_window(big, 1000) and tt < 10, tt
    same = [200_000_000] * 200_000                 # 판정이 늘 끝까지 훑는 입력
    t0 = time.perf_counter()
    assert solution(same, 200_000) == 200_000_000
    tt = max(tt, time.perf_counter() - t0)
    print(f"200k stones: {tt:.2f}s")
    print("ALL CHECKS PASSED")
