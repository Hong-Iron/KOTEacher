"""05.정렬과 정렬 기준: 병합 정렬을 직접 구현하고 문서의 주장을 확인한다."""
import random


def merge_sort(a, key=lambda x: x):
    """a를 key 순으로 정렬한 새 리스트를 돌려준다. 같은 key는 원래 순서를 지킨다(안정)."""
    if len(a) <= 1:
        return a[:]
    mid = len(a) // 2
    left, right = merge_sort(a[:mid], key), merge_sort(a[mid:], key)
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):     # 같으면 왼쪽(원래 앞)을 먼저: 안정성
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    out.extend(left[i:]); out.extend(right[j:])
    return out


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    rng = random.Random(5)
    for _ in range(2000):
        n = rng.randint(0, 30)
        a = [(rng.randint(0, 5), i) for i in range(n)]     # (키, 원래 위치)
        got = merge_sort(a, key=lambda p: p[0])
        check(got == sorted(a, key=lambda p: p[0]), "sorted와 다름")
        for x, y in zip(got, got[1:]):                      # 같은 키끼리 원래 순서
            if x[0] == y[0]:
                check(x[1] < y[1], "안정성 위반")
    check(merge_sort([5, 2, 4, 1, 3]) == [1, 2, 3, 4, 5], "표의 예")

    students = [("민수", 80), ("지아", 95), ("도윤", 80)]
    check(sorted(students, key=lambda s: (-s[1], s[0])) == [("지아", 95), ("도윤", 80), ("민수", 80)], "예시")
    check(sorted(students, key=lambda s: -s[1]) == [("지아", 95), ("민수", 80), ("도윤", 80)], "점수만: 80점끼리 원래 순서")
    a = [3, 1, 2]
    b = sorted(a)
    check(a == [3, 1, 2] and b == [1, 2, 3], "sorted는 새 리스트")
    check(a.sort() is None and a == [1, 2, 3], "sort는 None을 돌려준다")
    check(sorted([3, 1, 2], reverse=True) == [3, 2, 1], "reverse")
    check(sorted(["ccc", "a", "bb"], key=len) == ["a", "bb", "ccc"], "key=len")
    d = {"x": 3, "y": 1}
    check(sorted(d.items(), key=lambda kv: kv[1]) == [("y", 1), ("x", 3)], "값 순")
    check("B" < "a" and "10" < "9", "문자열 비교")
    people = [("b", 2), ("a", 1), ("c", 2)]
    people.sort(key=lambda p: p[0], reverse=True)
    people.sort(key=lambda p: p[1])
    check(people == [("a", 1), ("c", 2), ("b", 2)], "두 번 정렬")
    # 확인 문제
    words = ["b", "A", "a", "B"]
    check(sorted(words) == ["A", "B", "a", "b"] and sorted(words, key=str.lower) == ["A", "a", "b", "B"], "C1")
    w2 = ["bb", "a", "ccc", "aa", "c"]
    check(sorted(w2, key=lambda w: (-len(w), w)) == ["ccc", "aa", "bb", "a", "c"], "C2")
    check(sorted(["10", "9", "2"]) == ["10", "2", "9"] and sorted(["10", "9", "2"], key=int) == ["2", "9", "10"], "C3")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
