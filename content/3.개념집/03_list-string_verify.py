"""03.리스트와 문자열 문서의 주장을 확인한다."""
import time


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    a = [10, 20, 30, 40, 50]
    check(a[0] == 10 and a[4] == 50 and a[-1] == 50 and a[-5] == 10 and len(a) == 5, "번호")
    try:
        a[5]
        check(False, "IndexError가 나야 한다")
    except IndexError:
        pass
    check(a[1:4] == [20, 30, 40] and a[:2] == [10, 20] and a[3:] == [40, 50], "자르기")
    check(a[::2] == [10, 30, 50] and a[::-1] == [50, 40, 30, 20, 10], "건너뛰기, 거꾸로")
    b = a[1:3]
    b[0] = 99
    check(a == [10, 20, 30, 40, 50], "슬라이스는 복사본")
    check([x * x for x in range(5)] == [0, 1, 4, 9, 16], "컴프리헨션")
    evens = []
    for x in a:
        if x % 20 == 0:
            evens.append(x)
    check(evens == [x for x in a if x % 20 == 0] == [20, 40], "컴프리헨션 = 반복문")
    grid = [[0] * 4 for _ in range(3)]
    grid[1][2] = 7
    check(grid == [[0, 0, 0, 0], [0, 0, 7, 0], [0, 0, 0, 0]], "2차원 리스트")
    bad = [[0] * 3] * 2
    bad[0][0] = 1
    check(bad == [[1, 0, 0], [1, 0, 0]] and bad[0] is bad[1], "같은 줄을 가리킨다 (C2)")
    s = "hello"
    check(s[0] == "h" and s[1:3] == "el" and "H" + s[1:] == "Hello", "문자열 번호")
    try:
        s[0] = "H"
        check(False, "문자열은 고칠 수 없다")
    except TypeError:
        pass
    check("a b  c".split() == ["a", "b", "c"], "split()")
    check("2021.05.02".split(".") == ["2021", "05", "02"], "split('.')")
    check("-".join(["a", "b", "c"]) == "a-b-c", "join")
    check("banana".replace("an", "_") == "b__a", "replace")
    check("banana".find("na") == 2 and "banana".count("a") == 3, "find, count")
    check("abc123".isdigit() is False and "123".isdigit() is True, "isdigit")
    check("Hi".lower() == "hi" and "Hi".upper() == "HI", "lower, upper")
    check(ord("a") == 97 and chr(98) == "b", "ord, chr")
    check("na" in "banana", "부분 문자열 in")
    # C1
    a = [3, 1, 4, 1, 5]
    a.append(9)
    a.pop(0)
    b = a[1:3]
    b[0] = 7
    check(a == [1, 4, 1, 5, 9] and b == [7, 1], "C1")
    # C3
    words = ["ab", "cat", "dove", "x"]
    result = []
    for w in words:
        if len(w) >= 3:
            result.append(w.upper())
    check(result == [w.upper() for w in words if len(w) >= 3] == ["CAT", "DOVE"], "C3")
    # 1부터 센 i~j번째 = a[i-1:j]
    arr = [1, 5, 2, 6, 3, 7, 4]
    check(arr[2 - 1:5] == [5, 2, 6, 3], "1부터 센 구간")
    # pop(0)은 pop()보다 훨씬 느리다
    n = 100_000
    x = list(range(n))
    t = time.perf_counter()
    while x:
        x.pop()
    t_end = time.perf_counter() - t
    x = list(range(n))
    t = time.perf_counter()
    while x:
        x.pop(0)
    t_front = time.perf_counter() - t
    print(f"pop() {t_end:.4f}초, pop(0) {t_front:.4f}초, {t_front / t_end:.0f}배")
    check(t_front > 10 * t_end, "pop(0)이 훨씬 느려야 한다")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
