"""[1차] 추석 트래픽 (프로그래머스 17676) 풀이와 검증."""
import random
import time


def to_ms(clock):
    """'hh:mm:ss.sss' → 하루 시작부터의 밀리초."""
    h, m, s = clock.split(":")
    return (int(h) * 3600 + int(m) * 60) * 1000 + int(s.replace(".", ""))


def dur_ms(text):
    """'2s', '2.0s', '0.351s' → 밀리초. 소수점 아래를 글자로 다룬다."""
    sec, _, frac = text[:-1].partition(".")
    return int(sec) * 1000 + int((frac + "000")[:3])


def solution(lines):
    logs = []
    for line in lines:
        _, clock, dur = line.split()
        end = to_ms(clock)
        start = end - dur_ms(dur) + 1          # 시작과 끝 모두 포함
        logs.append((start, end))
    best = 0
    for _, e in logs:                          # 창: e ~ e + 999
        cnt = 0
        for s2, e2 in logs:
            if s2 <= e + 999 and e2 >= e:
                cnt += 1
        best = max(best, cnt)
    return best


def by_every_ms(lines):
    """창의 시작을 가능한 모든 밀리초로 옮겨 보는 풀이."""
    logs = []
    for line in lines:
        _, clock, dur = line.split()
        end = round(float(clock.split(":")[2]) * 1000) + (int(clock[:2]) * 3600 + int(clock[3:5]) * 60) * 1000
        logs.append((end - round(float(dur[:-1]) * 1000) + 1, end))
    lo = min(s for s, _ in logs) - 999
    hi = max(e for _, e in logs)
    best = 0
    for t in range(lo, hi + 1):
        best = max(best, sum(1 for s, e in logs if s <= t + 999 and e >= t))
    return best


def fmt(ms):
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


if __name__ == "__main__":
    assert solution(["2016-09-15 01:00:04.001 2.0s", "2016-09-15 01:00:07.000 2s"]) == 1
    assert solution(["2016-09-15 01:00:04.002 2.0s", "2016-09-15 01:00:07.000 2s"]) == 2
    ex3 = ["2016-09-15 20:59:57.421 0.351s", "2016-09-15 20:59:58.233 1.181s", "2016-09-15 20:59:58.299 0.8s",
           "2016-09-15 20:59:58.688 1.041s", "2016-09-15 20:59:59.591 1.412s", "2016-09-15 21:00:00.464 1.466s",
           "2016-09-15 21:00:00.741 1.581s", "2016-09-15 21:00:00.748 2.31s", "2016-09-15 21:00:00.966 0.381s",
           "2016-09-15 21:00:02.066 2.62s"]
    assert solution(ex3) == 7
    # 변환 확인
    assert to_ms("01:00:04.001") == 3604001
    assert dur_ms("2s") == dur_ms("2.0s") == 2000 and dur_ms("0.351s") == 351 and dur_ms("1.005s") == 1005
    assert int(float("1.005") * 1000) == 1004             # float로 바꾸면 1밀리초 틀린다
    # 6단계 추적: 예시 2
    s1, e1 = to_ms("01:00:04.002") - 2000 + 1, to_ms("01:00:04.002")
    s2, e2 = to_ms("01:00:07.000") - 2000 + 1, to_ms("01:00:07.000")
    assert (fmt(s1), fmt(e1), fmt(s2), fmt(e2)) == ("01:00:02.003", "01:00:04.002", "01:00:05.001", "01:00:07.000")
    assert fmt(e1 + 999) == "01:00:05.001" and fmt(e2 + 999) == "01:00:07.999"
    assert "2".partition(".") == ("2", "", "") and 24 * 3600 * 1000 * 2000 == 172_800_000_000
    # 무작위 비교
    rng = random.Random(17676)
    for _ in range(300):
        base = rng.randint(3600000, 7200000)
        ends = sorted(base + rng.randint(0, 6000) for _ in range(rng.randint(1, 8)))
        lines = []
        for e in ends:
            d = rng.randint(1, 3000)
            txt = f"{d // 1000}.{d % 1000:03d}".rstrip("0").rstrip(".") + "s"
            lines.append("2016-09-15 " + fmt(e) + " " + txt)
        assert solution(lines) == by_every_ms(lines), lines
    # 로그 2,000개 최악 시간
    big = ["2016-09-15 " + fmt(3600000 + i) + " 3.000s" for i in range(2000)]
    t0 = time.perf_counter()
    assert solution(big) == 2000
    print(f"2000 logs {time.perf_counter() - t0:.2f}s")
    print("ALL CHECKS PASSED")
