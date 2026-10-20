"""주차 요금 계산 (프로그래머스 92341) 풀이와 검증."""
import math
import random


def solution(fees, records):
    base_t, base_fee, unit_t, unit_fee = fees

    def minutes(hhmm):
        h, m = map(int, hhmm.split(":"))
        return h * 60 + m

    in_time = {}
    total = {}
    for r in records:
        t, car, kind = r.split()
        if kind == "IN":
            in_time[car] = minutes(t)
        else:
            total[car] = total.get(car, 0) + minutes(t) - in_time.pop(car)
    for car, t in in_time.items():
        total[car] = total.get(car, 0) + minutes("23:59") - t
    answer = []
    for car in sorted(total):
        over = max(0, total[car] - base_t)
        answer.append(base_fee + (over + unit_t - 1) // unit_t * unit_fee)
    return answer


def by_minutes(fees, records):
    """1분마다 주차장 안에 있는 차를 센다. [들어온 분, 나간 분) 동안 1분씩."""
    events = {}
    for r in records:
        t, car, kind = r.split()
        events.setdefault(int(t[:2]) * 60 + int(t[3:]), []).append((car, kind))
    inside, used = set(), {}
    for minute in range(24 * 60):
        for car, kind in events.get(minute, []):
            if kind == "IN":
                inside.add(car)
                used.setdefault(car, 0)
            else:
                inside.discard(car)
        for car in inside:
            if minute < 23 * 60 + 59:
                used[car] += 1
    out = []
    for car in sorted(used):
        u = used[car]
        fee = fees[1]
        if u > fees[0]:
            fee += math.ceil((u - fees[0]) / fees[2]) * fees[3]
        out.append(fee)
    return out


def rand_records(rng):
    cars = [f"{rng.randint(0, 9999):04d}" for _ in range(rng.randint(1, 4))]
    evs = []
    for c in set(cars):
        pts = sorted(rng.sample(range(0, 1439), rng.choice([1, 2, 3, 4, 5, 6])))
        for i, p in enumerate(pts):
            evs.append((p, c, "IN" if i % 2 == 0 else "OUT"))
    evs.sort()
    # 같은 분에 같은 차가 두 번 나오지 않게 sample로 뽑았다
    return [f"{p // 60:02d}:{p % 60:02d} {c} {k}" for p, c, k in evs]


if __name__ == "__main__":
    assert solution([180, 5000, 10, 600], ["05:34 5961 IN", "06:00 0000 IN", "06:34 0000 OUT", "07:59 5961 OUT",
                                           "07:59 0148 IN", "18:59 0000 IN", "19:09 0148 OUT", "22:59 5961 IN",
                                           "23:00 5961 OUT"]) == [14600, 34400, 5000]
    assert solution([120, 0, 60, 591], ["16:00 3961 IN", "16:00 0202 IN", "18:00 3961 OUT", "18:00 0202 OUT",
                                        "23:58 3961 IN"]) == [0, 591]
    assert solution([1, 461, 1, 10], ["00:00 1234 IN"]) == [14841]
    assert solution([60, 1000, 10, 100], ["08:00 1111 IN", "10:15 1111 OUT", "22:00 2222 IN"]) == [1800, 1600]
    rng = random.Random(92341)
    for _ in range(2000):
        fees = [rng.randint(1, 300), rng.randint(0, 5000), rng.randint(1, 60), rng.randint(1, 1000)]
        recs = rand_records(rng)
        assert solution(fees, recs) == by_minutes(fees, recs), (fees, recs)
    print("ALL CHECKS PASSED")
