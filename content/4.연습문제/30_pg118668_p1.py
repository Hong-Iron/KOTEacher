"""코딩 테스트 공부 (프로그래머스 118668) 풀이와 검증."""
import heapq
import random
import time


def solution(alp, cop, problems):
    A = max(p[0] for p in problems)          # 목표 알고력
    C = max(p[1] for p in problems)          # 목표 코딩력
    alp, cop = min(alp, A), min(cop, C)      # 목표를 넘는 힘은 목표로 친다
    INF = float("inf")
    dp = [[INF] * (C + 1) for _ in range(A + 1)]
    dp[alp][cop] = 0
    for a in range(alp, A + 1):
        for c in range(cop, C + 1):
            t = dp[a][c]
            if t == INF:
                continue
            if a < A and t + 1 < dp[a + 1][c]:          # 알고리즘 공부
                dp[a + 1][c] = t + 1
            if c < C and t + 1 < dp[a][c + 1]:          # 코딩 공부
                dp[a][c + 1] = t + 1
            for ra, rc, wa, wc, cost in problems:
                if a >= ra and c >= rc:                 # 풀 수 있는 문제
                    na, nc = min(A, a + wa), min(C, c + wc)
                    if (na, nc) != (a, c) and t + cost < dp[na][nc]:
                        dp[na][nc] = t + cost
    return dp[A][C]


def by_dijkstra(alp, cop, problems):
    """목표를 넘는 값도 그대로 두고(상한만 넉넉히), 다익스트라로 '둘 다 목표 이상'인 첫 상태를 찾는다."""
    A = max(p[0] for p in problems)
    C = max(p[1] for p in problems)
    # 쓸모 있는 풀이는 알고력이나 코딩력을 1 이상 올리니 A + C번이면 충분하다. 그만큼 오를 수 있는 값까지 둔다.
    wa_max = max([p[2] for p in problems] + [1])
    wc_max = max([p[3] for p in problems] + [1])
    capA = max(A, alp) + wa_max * (A + C + 2)
    capC = max(C, cop) + wc_max * (A + C + 2)
    dist = {(alp, cop): 0}
    h = [(0, alp, cop)]
    while h:
        t, a, c = heapq.heappop(h)
        if t > dist[(a, c)]:
            continue
        if a >= A and c >= C:
            return t
        moves = [(a + 1, c, 1), (a, c + 1, 1)]
        for ra, rc, wa, wc, cost in problems:
            if a >= ra and c >= rc:
                moves.append((a + wa, c + wc, cost))
        for na, nc, w in moves:
            if na <= capA and nc <= capC and t + w < dist.get((na, nc), float("inf")):
                dist[(na, nc)] = t + w
                heapq.heappush(h, (t + w, na, nc))
    return None


if __name__ == "__main__":
    assert solution(10, 10, [[10, 15, 2, 1, 2], [20, 20, 3, 3, 4]]) == 15
    assert solution(0, 0, [[0, 0, 2, 1, 2], [4, 5, 3, 1, 2], [4, 11, 4, 0, 2], [10, 4, 0, 4, 2]]) == 13
    # 6단계 추적: 예시 1의 표 일부
    P1 = [[10, 15, 2, 1, 2], [20, 20, 3, 3, 4]]
    A, C = 20, 20
    INF = float("inf")
    dp = [[INF] * (C + 1) for _ in range(A + 1)]
    dp[10][10] = 0
    for a in range(10, A + 1):
        for c in range(10, C + 1):
            t = dp[a][c]
            if t == INF:
                continue
            if a < A:
                dp[a + 1][c] = min(dp[a + 1][c], t + 1)
            if c < C:
                dp[a][c + 1] = min(dp[a][c + 1], t + 1)
            for ra, rc, wa, wc, cost in P1:
                if a >= ra and c >= rc:
                    na, nc = min(A, a + wa), min(C, c + wc)
                    if (na, nc) != (a, c):
                        dp[na][nc] = min(dp[na][nc], t + cost)
    assert [dp[10][15], dp[12][16], dp[14][17], dp[16][18], dp[18][19], dp[20][20]] == [5, 7, 9, 11, 13, 15]
    assert dp[20][10] == 10 and dp[10][20] == 10 and dp[20][20] == 15
    # 알고력이 목표를 한참 넘어도 코딩력을 위해 같은 문제를 계속 푸는 경우
    assert solution(1, 3, [[16, 18, 2, 2, 7], [13, 2, 5, 2, 1]]) == 20 == by_dijkstra(1, 3, [[16, 18, 2, 2, 7], [13, 2, 5, 2, 1]])
    # 이미 모두 풀 수 있으면 0
    assert solution(150, 150, [[10, 10, 1, 1, 1]]) == 0
    # 무작위 비교(정확성 테스트 크기)
    rng = random.Random(118668)
    for _ in range(600):
        probs = [[rng.randint(0, 20), rng.randint(0, 20), rng.randint(0, 5), rng.randint(0, 5), rng.randint(1, 10)]
                 for _ in range(rng.randint(1, 6))]
        a0, c0 = rng.randint(0, 20), rng.randint(0, 20)
        assert solution(a0, c0, probs) == by_dijkstra(a0, c0, probs), (a0, c0, probs)
    # 효율성 크기: 목표 150, 문제 100개
    probs = [[rng.randint(0, 150), rng.randint(0, 150), rng.randint(0, 30), rng.randint(0, 30), rng.randint(1, 100)]
             for _ in range(99)] + [[150, 150, 0, 0, 1]]
    t0 = time.perf_counter()
    solution(0, 0, probs)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"151x151 x 100 problems: {t:.2f}s")
    print("ALL CHECKS PASSED")
