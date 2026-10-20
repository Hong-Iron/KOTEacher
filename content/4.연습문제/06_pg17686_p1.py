"""파일명 정렬 (프로그래머스 17686) 풀이와 검증."""
import random
import re
from functools import cmp_to_key


def solution(files):
    def key(f):
        head, number = re.match(r"(\D+)(\d{1,5})", f).groups()
        return (head.lower(), int(number))
    return sorted(files, key=key)


def by_compare(files):
    def split(f):
        i = 0
        while not f[i].isdigit():
            i += 1
        j = i
        while j < len(f) and f[j].isdigit() and j - i < 5:
            j += 1
        return f[:i].lower(), int(f[i:j])

    items = [(split(f), idx, f) for idx, f in enumerate(files)]

    def cmp(a, b):
        (ha, na), ia, _ = a
        (hb, nb), ib, _ = b
        if ha != hb:
            return -1 if ha < hb else 1
        if na != nb:
            return -1 if na < nb else 1
        return -1 if ia < ib else (1 if ia > ib else 0)

    return [f for _, _, f in sorted(items, key=cmp_to_key(cmp))]


def rand_name(rng):
    head = rng.choice("abAB") + "".join(rng.choice("abAB .-") for _ in range(rng.randint(0, 3)))
    num = "".join(rng.choice("0123456789") for _ in range(rng.randint(1, 7)))
    tail = "".join(rng.choice("ab.-0123 ") for _ in range(rng.randint(0, 4)))
    return head + num + tail


if __name__ == "__main__":
    assert solution(["img12.png", "img10.png", "img02.png", "img1.png", "IMG01.GIF", "img2.JPG"]) == \
        ["img1.png", "IMG01.GIF", "img02.png", "img2.JPG", "img10.png", "img12.png"]
    assert solution(["F-5 Freedom Fighter", "B-50 Superfortress", "A-10 Thunderbolt II", "F-14 Tomcat"]) == \
        ["A-10 Thunderbolt II", "B-50 Superfortress", "F-5 Freedom Fighter", "F-14 Tomcat"]
    assert solution(["b2.txt", "A10.txt", "a2.png", "a02.txt"]) == ["a2.png", "a02.txt", "A10.txt", "b2.txt"]
    assert re.match(r"(\D+)(\d{1,5})", "img123456.png").groups() == ("img", "12345")
    rng = random.Random(17686)
    for _ in range(2000):
        files = list({rand_name(rng) for _ in range(rng.randint(1, 12))})
        rng.shuffle(files)
        assert solution(files) == by_compare(files), files
    print("ALL CHECKS PASSED")
