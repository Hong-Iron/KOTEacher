"""거리두기 확인하기 (프로그래머스 81302) 풀이와 검증."""
import random
from collections import deque


def solution(places):
    answer = []
    for room in places:
        people = [(r, c) for r in range(5) for c in range(5) if room[r][c] == "P"]
        ok = 1
        for i in range(len(people)):
            for j in range(i + 1, len(people)):
                (r1, c1), (r2, c2) = people[i], people[j]
                d = abs(r1 - r2) + abs(c1 - c2)
                if d == 1:
                    ok = 0
                elif d == 2:
                    if r1 == r2:
                        if room[r1][(c1 + c2) // 2] != "X":
                            ok = 0
                    elif c1 == c2:
                        if room[(r1 + r2) // 2][c1] != "X":
                            ok = 0
                    elif room[r1][c2] != "X" or room[r2][c1] != "X":
                        ok = 0
        answer.append(ok)
    return answer


def by_bfs(places):
    out = []
    for room in places:
        ok = 1
        for sr in range(5):
            for sc in range(5):
                if room[sr][sc] != "P":
                    continue
                q, seen = deque([(sr, sc, 0)]), {(sr, sc)}
                while q:
                    r, c, d = q.popleft()
                    if d > 0 and room[r][c] == "P":
                        ok = 0
                    if d == 2:
                        continue
                    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                        if 0 <= nr < 5 and 0 <= nc < 5 and (nr, nc) not in seen and room[nr][nc] != "X":
                            seen.add((nr, nc))
                            q.append((nr, nc, d + 1))
        out.append(ok)
    return out


if __name__ == "__main__":
    ex = [["POOOP", "OXXOX", "OPXPX", "OOXOX", "POXXP"], ["POOPX", "OXPXP", "PXXXO", "OXXXO", "OOOPP"],
          ["PXOPX", "OXOXP", "OXPOX", "OXXOP", "PXPOX"], ["OOOXX", "XOOOX", "OOOXX", "OXOOX", "OOOOO"],
          ["PXPXP", "XPXPX", "PXPXP", "XPXPX", "PXPXP"]]
    assert solution(ex) == [1, 0, 1, 1, 1] == by_bfs(ex)
    rng = random.Random(81302)
    for _ in range(3000):
        rooms = [["".join(rng.choice("PPOOX") for _ in range(5)) for _ in range(5)] for _ in range(5)]
        assert solution(rooms) == by_bfs(rooms), rooms
    print("ALL CHECKS PASSED")
