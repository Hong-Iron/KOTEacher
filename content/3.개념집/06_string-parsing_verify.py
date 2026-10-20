"""06.문자열 파싱과 정규 표현식 문서의 주장을 확인한다."""
import random
import re


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def by_reading(s):
    i, parts = 0, []
    while i < len(s):
        j = i
        while s[j].isdigit():
            j += 1
        num, bonus = int(s[i:j]), s[j]
        j += 1
        opt = ""
        if j < len(s) and s[j] in "*#":
            opt = s[j]
            j += 1
        parts.append((num, bonus, opt))
        i = j
    return parts


def by_regex(s):
    return [(int(a), b, c) for a, b, c in re.findall(r"(\d+)([SDT])([*#]?)", s)]


def main():
    h, m = "10:20".split(":")
    check((int(h), int(m)) == (10, 20), "split")
    want = [(1, "S", ""), (2, "D", "*"), (3, "T", "")]
    check(by_reading("1S2D*3T") == want == by_regex("1S2D*3T"), "세 방법")
    check(re.findall(r"(\d+)([SDT])([*#]?)", "1S2D*3T") == [("1", "S", ""), ("2", "D", "*"), ("3", "T", "")], "findall 결과")
    rng = random.Random(6)
    for _ in range(1000):
        s = "".join(f"{rng.randint(0, 10)}{rng.choice('SDT')}{rng.choice(['', '*', '#'])}" for _ in range(3))
        check(by_reading(s) == by_regex(s), s)
    # 기호 표
    check(re.fullmatch(r"\d\d", "05") and re.fullmatch(r"[SDT]", "D"), "\\d, []")
    check(re.fullmatch(r"[a-z0-9]", "k") and re.fullmatch(r"[a-z0-9]", "7") and re.fullmatch(r"[^0-9]", "x"), "범위, 부정")
    check(re.fullmatch(r"a.c", "abc") and re.fullmatch(r"a.c", "a-c") and re.fullmatch(r"\d+\.\d+", "3.14"), ". 과 \\.")
    check(not re.fullmatch(r"\d+\.\d+", "3x14") and re.fullmatch(r"\d+.\d+", "3x14"), "점의 특별한 뜻")
    check(re.fullmatch(r"\d+", "2024") and re.fullmatch(r"ab*", "a") and re.fullmatch(r"ab*", "abbb"), "+, *")
    check(re.fullmatch(r"[*#]?", "") and re.fullmatch(r"[*#]?", "*"), "?")
    check(re.fullmatch(r"\.{2,}", "..") and re.fullmatch(r"\.{2,}", "....") and not re.fullmatch(r"\.{2,}", "."), "{2,}")
    check(re.sub(r"^\.", "", ".a.") == "a.", "^")
    check(re.findall(r"(\d+)-(\d+)", "3-45") == [("3", "45")], "( )")
    check(re.sub(r"[^a-z0-9]", "", "Hi! a-1") == "ia1", "sub 예1 실제 값")
    check(re.sub(r"\.{2,}", ".", "a...b..c") == "a.b.c", "sub 예2")
    check("a  b".split(" ") == ["a", "", "b"] and "a  b".split() == ["a", "b"], "split 빈 조각")
    # 확인 문제
    check(re.findall(r"\d+", "a12b3c045") == ["12", "3", "045"], "C1")
    check(by_reading("10S2D") == [(10, "S", ""), (2, "D", "")], "C2")
    check("2022.05.19".split(".") == ["2022", "05", "19"], "C3 가")
    check(re.sub(r"[^a-z0-9]", "", "...!@BaT#".lower()) == "bat", "C3 나")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
