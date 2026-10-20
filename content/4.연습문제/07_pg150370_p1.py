"""개인정보 수집 유효기간 (프로그래머스 150370) 풀이와 검증."""
import random


def solution(today, terms, privacies):
    def to_day(date):
        y, m, d = map(int, date.split("."))
        return y * 12 * 28 + (m - 1) * 28 + d

    now = to_day(today)
    months = {}
    for t in terms:
        kind, m = t.split()
        months[kind] = int(m)
    answer = []
    for i, p in enumerate(privacies, 1):
        date, kind = p.split()
        if to_day(date) + months[kind] * 28 <= now:
            answer.append(i)
    return answer


def literal(today, terms, privacies):
    """월을 직접 더하고 넘치면 연도로 넘긴 뒤, '보관 가능한 마지막 날'과 오늘을 (연, 월, 일)로 비교한다."""
    ty, tm, td = map(int, today.split("."))
    months = {k: int(v) for k, v in (t.split() for t in terms)}
    out = []
    for i, p in enumerate(privacies, 1):
        date, kind = p.split()
        y, m, d = map(int, date.split("."))
        m += months[kind]
        while m > 12:
            m -= 12
            y += 1
        d -= 1                    # 전날까지 보관
        if d == 0:
            d = 28
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        if (ty, tm, td) > (y, m, d):
            out.append(i)
    return out


def rand_date(rng):
    return f"{rng.randint(2000, 2022)}.{rng.randint(1, 12):02d}.{rng.randint(1, 28):02d}"


if __name__ == "__main__":
    assert solution("2022.05.19", ["A 6", "B 12", "C 3"],
                    ["2021.05.02 A", "2021.07.01 B", "2022.02.19 C", "2022.02.20 C"]) == [1, 3]
    assert solution("2020.01.01", ["Z 3", "D 5"],
                    ["2019.01.01 D", "2019.11.15 Z", "2019.08.02 D", "2019.07.01 D", "2018.12.28 Z"]) == [1, 4, 5]
    rng = random.Random(150370)
    for _ in range(2000):
        kinds = rng.sample("ABCDEFGHIJ", rng.randint(1, 5))
        terms = [f"{k} {rng.randint(1, 100)}" for k in kinds]
        today = rand_date(rng)
        privacies = [f"{rand_date(rng)} {rng.choice(kinds)}" for _ in range(rng.randint(1, 10))]
        assert solution(today, terms, privacies) == literal(today, terms, privacies)
    print("ALL CHECKS PASSED")
