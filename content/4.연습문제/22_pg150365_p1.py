"""미로 탈출 명령어 (프로그래머스 150365) 풀이와 검증."""
import random
from itertools import product

MOVES = [("d", 1, 0), ("l", 0, -1), ("r", 0, 1), ("u", -1, 0)]      # 사전 순


def solution(n, m, x, y, r, c, k):
    dist = abs(x - r) + abs(y - c)
    if dist > k or (k - dist) % 2 == 1:
        return "impossible"
    path = []
    for step in range(k):
        remain = k - step - 1                # 이번 걸음 뒤에 남는 걸음 수
        for ch, dx, dy in MOVES:
            nx, ny = x + dx, y + dy
            if 1 <= nx <= n and 1 <= ny <= m and abs(nx - r) + abs(ny - c) <= remain:
                x, y = nx, ny
                path.append(ch)
                break
    return "".join(path)


def trace(n, m, x, y, r, c, k):
    rows = []
    for step in range(k):
        remain = k - step - 1
        tried = []
        for ch, dx, dy in MOVES:
            nx, ny = x + dx, y + dy
            if not (1 <= nx <= n and 1 <= ny <= m):
                tried.append((ch, "밖"))
                continue
            d = abs(nx - r) + abs(ny - c)
            tried.append((ch, d))
            if d <= remain:
                x, y = nx, ny
                break
        rows.append((remain, tried, (x, y)))
    return rows


def by_all_strings(n, m, x, y, r, c, k):
    """길이 k 문자열을 사전 순으로 모두 만들어, 처음으로 규칙에 맞는 것을 돌려준다."""
    step = {ch: (dx, dy) for ch, dx, dy in MOVES}
    for s in product("dlru", repeat=k):
        px, py, good = x, y, True
        for ch in s:
            px, py = px + step[ch][0], py + step[ch][1]
            if not (1 <= px <= n and 1 <= py <= m):
                good = False
                break
        if good and (px, py) == (r, c):
            return "".join(s)
    return "impossible"


if __name__ == "__main__":
    assert solution(3, 4, 2, 3, 3, 1, 5) == "dllrl"
    assert solution(2, 2, 1, 1, 2, 2, 2) == "dr"
    assert solution(3, 3, 1, 2, 3, 3, 4) == "impossible"
    # 6단계 추적
    assert trace(3, 4, 2, 3, 3, 1, 5) == [
        (4, [("d", 2)], (3, 3)),
        (3, [("d", "밖"), ("l", 1)], (3, 2)),
        (2, [("d", "밖"), ("l", 0)], (3, 1)),
        (1, [("d", "밖"), ("l", "밖"), ("r", 1)], (3, 2)),
        (0, [("d", "밖"), ("l", 0)], (3, 1)),
    ]
    # 무작위 비교: 모든 문자열을 사전 순으로 보는 풀이
    rng = random.Random(150365)
    for _ in range(1500):
        n, m = rng.randint(2, 4), rng.randint(2, 4)
        x, y = rng.randint(1, n), rng.randint(1, m)
        r, c = rng.randint(1, n), rng.randint(1, m)
        if (x, y) == (r, c):
            continue
        k = rng.randint(1, 7)
        assert solution(n, m, x, y, r, c, k) == by_all_strings(n, m, x, y, r, c, k), (n, m, x, y, r, c, k)
    # 가장 큰 입력
    assert len(solution(50, 50, 1, 1, 50, 50, 2500)) == 2500
    assert 4 ** 2500 > 10 ** 1500
    print("ALL CHECKS PASSED")
