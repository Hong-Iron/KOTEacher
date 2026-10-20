"""신규 아이디 추천 (프로그래머스 72410) 풀이와 검증."""
import random
import re


def solution(new_id):
    s = new_id.lower()
    s = re.sub(r"[^a-z0-9\-_.]", "", s)
    s = re.sub(r"\.+", ".", s)
    s = s.strip(".")
    s = s or "a"
    s = s[:15].rstrip(".")
    s = s + s[-1] * (3 - len(s))
    return s


def literal(new_id):
    """정규 표현식 없이 문제의 7단계를 글자 단위로 따른다."""
    s = new_id.lower()
    s = "".join(ch for ch in s if ch.islower() and ch.isascii() or ch.isdigit() or ch in "-_.")
    out = []
    for ch in s:
        if ch == "." and out and out[-1] == ".":
            continue
        out.append(ch)
    s = "".join(out)
    if s.startswith("."):
        s = s[1:]
    if s.endswith("."):
        s = s[:-1]
    if s == "":
        s = "a"
    if len(s) >= 16:
        s = s[:15]
        if s.endswith("."):
            s = s[:-1]
    while len(s) <= 2:
        s += s[-1]
    return s


if __name__ == "__main__":
    ex = [("...!@BaT#*..y.abcdefghijklm", "bat.y.abcdefghi"), ("z-+.^.", "z--"), ("=.=", "aaa"),
          ("123_.def", "123_.def"), ("abcdefghijklmn.p", "abcdefghijklmn"), ("..A!b..c.", "ab.c")]
    for s, want in ex:
        assert solution(s) == want == literal(s), s
    assert "a...b".replace("..", ".") == "a..b"            # replace 한 번으로는 부족
    alphabet = "abcXYZ019-_.~!@#$%^&*()=+[{]}:?,<>/"
    rng = random.Random(72410)
    for _ in range(3000):
        s = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 30)))
        assert solution(s) == literal(s), s
    print("ALL CHECKS PASSED")
