"""07.시간·날짜 계산 문서의 주장을 확인한다."""
import math


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def to_str(x):
    h, m = divmod(x, 60)
    return f"{h:02d}:{m:02d}"


def to_day(date):
    y, m, d = map(int, date.split("."))
    return y * 12 * 28 + (m - 1) * 28 + d


def main():
    for x in range(24 * 60):
        check(to_min(to_str(x)) == x, f"왕복 {x}")
    check(to_min("09:05") == 545 and to_min("10:02") == 602 and to_min("10:02") - to_min("09:05") == 57, "예시")
    check(divmod(545, 60) == (9, 5) and to_str(545) == "09:05", "되돌리기")
    check(f"{9:02d}" == "09" and f"{12:02d}" == "12", "02d")
    # 28일 달력: 하루 뒤는 1 크다, 달이 바뀌어도
    check(to_day("2022.05.28") + 1 == to_day("2022.06.01"), "달 넘김")
    check(to_day("2022.12.28") + 1 == to_day("2023.01.01"), "해 넘김")
    for a in range(1, 501):
        for b in range(1, 61):
            check((a + b - 1) // b == -(-a // b) == math.ceil(a / b), f"올림 {a} {b}")
    # 확인 문제
    diff = to_min("00:15") - to_min("23:40")
    if diff < 0:
        diff += 1440
    check(diff == 35, "C1")
    h, m = divmod(125, 60)
    check(f"{h:02d}:{m:02d}" == "02:05", "C3")
    check(("9:05" < "10:02") is False and ("09:05" < "10:02") is True, "문자열 비교 함정")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
