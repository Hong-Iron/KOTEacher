"""셔틀버스 (프로그래머스 17678) 풀이와 검증."""
import random


def solution(n, t, m, timetable):
    crew = sorted(int(x[:2]) * 60 + int(x[3:]) for x in timetable)
    idx = 0
    for i in range(n):
        bus = 540 + i * t
        riders = []
        while len(riders) < m and idx < len(crew) and crew[idx] <= bus:
            riders.append(crew[idx])
            idx += 1
    ans = bus if len(riders) < m else riders[-1] - 1
    return f"{ans // 60:02d}:{ans % 60:02d}"


def slow(n, t, m, timetable):
    crew = [int(x[:2]) * 60 + int(x[3:]) for x in timetable]
    for c in range(1439, -1, -1):
        # 콘은 같은 시각 크루 뒤에 선다: (시각, 0=크루/1=콘)으로 정렬
        queue = sorted([(x, 0) for x in crew] + [(c, 1)])
        pos = 0
        boarded = False
        for i in range(n):
            bus = 540 + i * t
            cnt = 0
            while cnt < m and pos < len(queue) and queue[pos][0] <= bus:
                if queue[pos][1] == 1:
                    boarded = True
                pos += 1
                cnt += 1
        if boarded:
            return f"{c // 60:02d}:{c % 60:02d}"
    return None


if __name__ == "__main__":
    ex = [(1, 1, 5, ["08:00", "08:01", "08:02", "08:03"], "09:00"),
          (2, 10, 2, ["09:10", "09:09", "08:00"], "09:09"),
          (2, 1, 2, ["09:00", "09:00", "09:00", "09:00"], "08:59"),
          (1, 1, 5, ["00:01", "00:01", "00:01", "00:01", "00:01"], "00:00"),
          (1, 1, 1, ["23:59"], "09:00"),
          (10, 60, 45, ["23:59"] * 16, "18:00"),
          (2, 10, 2, ["09:00", "09:05", "09:05"], "09:04")]
    for n, t, m, tt, want in ex:
        assert solution(n, t, m, tt) == want == slow(n, t, m, tt), (n, t, m, tt)
    rng = random.Random(17678)
    for _ in range(2000):
        n, t, m = rng.randint(1, 4), rng.randint(1, 20), rng.randint(1, 4)
        tt = [f"{rng.randint(8, 10):02d}:{rng.randint(0, 59):02d}" for _ in range(rng.randint(1, 12))]
        assert solution(n, t, m, tt) == slow(n, t, m, tt), (n, t, m, tt)
    print("ALL CHECKS PASSED")
