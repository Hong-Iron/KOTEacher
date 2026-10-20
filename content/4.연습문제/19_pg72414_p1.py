"""광고 삽입 (프로그래머스 72414) 풀이와 검증."""
import random
import time


def to_sec(t):
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


def to_str(x):
    return f"{x // 3600:02d}:{x % 3600 // 60:02d}:{x % 60:02d}"


def solution(play_time, adv_time, logs):
    P, A = to_sec(play_time), to_sec(adv_time)
    cnt = [0] * (P + 1)
    for log in logs:
        s, e = log.split("-")
        cnt[to_sec(s)] += 1
        cnt[to_sec(e)] -= 1                  # 끝 시각의 1초는 보지 않는다
    for i in range(1, P + 1):                # cnt[i]: i초 ~ i+1초를 보는 사람 수
        cnt[i] += cnt[i - 1]
    S = [0] * (P + 1)                        # S[t]: 0초 ~ t초의 누적 재생 시간
    for i in range(P):
        S[i + 1] = S[i] + cnt[i]
    best, best_t = -1, 0
    for t in range(P - A + 1):
        v = S[t + A] - S[t]
        if v > best:                         # 같으면 앞의 것을 남긴다
            best, best_t = v, t
    return to_str(best_t)


def by_overlap(play_time, adv_time, logs):
    """시작 시각마다 기록과 겹치는 길이를 직접 더한다."""
    P, A = to_sec(play_time), to_sec(adv_time)
    iv = [tuple(map(to_sec, log.split("-"))) for log in logs]
    best, best_t = -1, 0
    for t in range(P - A + 1):
        v = sum(max(0, min(e, t + A) - max(s, t)) for s, e in iv)
        if v > best:
            best, best_t = v, t
    return to_str(best_t)


if __name__ == "__main__":
    assert solution("02:03:55", "00:14:15", ["01:20:15-01:45:14", "00:40:31-01:00:00", "00:25:50-00:48:29",
                                             "01:30:59-01:53:29", "01:37:44-02:02:30"]) == "01:30:59"
    assert solution("99:59:59", "25:00:00", ["69:59:59-89:59:59", "01:00:00-21:00:00", "79:59:59-99:59:59",
                                             "11:00:00-31:00:00"]) == "01:00:00"
    assert solution("50:00:00", "50:00:00", ["15:36:51-38:21:49", "10:14:18-15:36:51", "38:21:49-42:51:45"]) == "00:00:00"
    # 1단계·6단계의 작은 예: 동영상 10초, 광고 3초, 기록 1~4, 2~6, 5~9
    small = ["00:00:01-00:00:04", "00:00:02-00:00:06", "00:00:05-00:00:09"]
    assert solution("00:00:10", "00:00:03", small) == "00:00:01"
    cnt = [0] * 11
    for s, e in [(1, 4), (2, 6), (5, 9)]:
        cnt[s] += 1; cnt[e] -= 1
    assert cnt[:10] == [0, 1, 1, 0, -1, 1, -1, 0, 0, -1]
    for i in range(1, 11):
        cnt[i] += cnt[i - 1]
    assert cnt[:10] == [0, 1, 2, 2, 1, 2, 1, 1, 1, 0]
    S = [0]
    for i in range(10):
        S.append(S[-1] + cnt[i])
    assert S == [0, 0, 1, 3, 5, 6, 8, 9, 10, 11, 11]
    assert [S[t + 3] - S[t] for t in range(8)] == [3, 5, 5, 5, 4, 4, 3, 2]
    # 예시 1의 누적 재생 시간 36분
    P = to_sec("02:03:55")
    iv = [tuple(map(to_sec, x.split("-"))) for x in ["01:20:15-01:45:14", "00:40:31-01:00:00", "00:25:50-00:48:29",
                                                      "01:30:59-01:53:29", "01:37:44-02:02:30"]]
    t = to_sec("01:30:59")
    assert sum(max(0, min(e, t + to_sec("00:14:15")) - max(s, t)) for s, e in iv) == 36 * 60
    # 무작위 비교
    rng = random.Random(72414)
    for _ in range(1500):
        P = rng.randint(1, 60)
        A = rng.randint(1, P)
        logs = []
        for _ in range(rng.randint(1, 6)):
            s = rng.randint(0, P - 1)
            e = rng.randint(s + 1, P)
            logs.append(to_str(s) + "-" + to_str(e))
        assert solution(to_str(P), to_str(A), logs) == by_overlap(to_str(P), to_str(A), logs), (P, A, logs)
    # 효율성: 99:59:59, 기록 30만 개
    logs = []
    for _ in range(300_000):
        s = rng.randint(0, 359_998)
        logs.append(to_str(s) + "-" + to_str(rng.randint(s + 1, 359_999)))
    t0 = time.perf_counter()
    solution("99:59:59", "01:00:00", logs)
    tt = time.perf_counter() - t0
    assert tt < 10, tt
    print(f"300k logs: {tt:.2f}s")
    print("ALL CHECKS PASSED")
