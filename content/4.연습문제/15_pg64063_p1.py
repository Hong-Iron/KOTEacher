"""호텔 방 배정 (프로그래머스 64063) 풀이와 검증."""
import random
import time


def solution(k, room_number):
    nxt = {}                                  # nxt[x]: x번이 찼으면 다음에 알아볼 방

    def find(x):
        path = []
        while x in nxt:                       # 빈 방이 나올 때까지 따라간다
            path.append(x)
            x = nxt[x]
        for p in path:                        # 지나온 방들이 빈 방을 바로 가리키게(경로 압축)
            nxt[p] = x
        return x

    answer = []
    for want in room_number:
        r = find(want)
        answer.append(r)
        nxt[r] = r + 1                        # r이 찼으니 다음부터는 r+1부터 알아본다
    return answer


def by_scan(k, room_number):
    used, out = set(), []
    for want in room_number:
        r = want
        while r in used:
            r += 1
        used.add(r)
        out.append(r)
    return out


if __name__ == "__main__":
    assert solution(10, [1, 3, 4, 1, 3, 1]) == [1, 3, 4, 2, 5, 6] == by_scan(10, [1, 3, 4, 1, 3, 1])
    # 6단계 추적: nxt의 변화
    nxt, snaps = {}, []

    def find(x):
        path = []
        while x in nxt:
            path.append(x)
            x = nxt[x]
        for p in path:
            nxt[p] = x
        return x
    for want in [1, 3, 4, 1, 3, 1]:
        r = find(want)
        nxt[r] = r + 1
        snaps.append((want, r, dict(sorted(nxt.items()))))
    assert snaps == [
        (1, 1, {1: 2}),
        (3, 3, {1: 2, 3: 4}),
        (4, 4, {1: 2, 3: 4, 4: 5}),
        (1, 2, {1: 2, 2: 3, 3: 4, 4: 5}),
        (3, 5, {1: 2, 2: 3, 3: 5, 4: 5, 5: 6}),
        (1, 6, {1: 6, 2: 6, 3: 6, 4: 5, 5: 6, 6: 7}),
    ], snaps
    rng = random.Random(64063)
    for _ in range(3000):
        k = rng.randint(1, 30)
        m = rng.randint(1, k)
        rooms = [rng.randint(1, max(1, k - m + 1)) for _ in range(m)]   # 모두 배정받을 수 있게
        assert solution(k, rooms) == by_scan(k, rooms), (k, rooms)
    # 효율성: 같은 방을 20만 번 원하면 한 방향으로 길게 이어진다
    t0 = time.perf_counter()
    res = solution(10 ** 12, [1] * 200_000)
    assert res == list(range(1, 200_001))
    big = [random.Random(1).randint(1, 10 ** 12 - 200_000) for _ in range(200_000)]
    solution(10 ** 12, big)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"200k customers x2: {t:.2f}s")
    print("ALL CHECKS PASSED")
