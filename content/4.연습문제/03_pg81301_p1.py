"""숫자 문자열과 영단어 (프로그래머스 81301) 풀이와 검증."""
import random

WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def solution(s):
    words = ["zero", "one", "two", "three", "four",
             "five", "six", "seven", "eight", "nine"]
    for i, w in enumerate(words):
        s = s.replace(w, str(i))
    return int(s)


if __name__ == "__main__":
    assert solution("one4seveneight") == 1478
    assert solution("23four5six7") == 234567
    assert solution("2three45sixseven") == 234567
    assert solution("123") == 123
    assert solution("two5zero") == 250
    # 어느 단어도 다른 단어 안에 통째로 들어 있지 않다 (바꾸는 순서가 상관없는 근거)
    assert not any(a != b and a in b for a in WORDS for b in WORDS)
    rng = random.Random(81301)
    for _ in range(2000):
        n = rng.randint(1, 2_000_000_000)
        s = "".join(WORDS[int(d)] if rng.random() < 0.5 else d for d in str(n))
        assert solution(s) == n, (s, n)
    print("ALL CHECKS PASSED")
