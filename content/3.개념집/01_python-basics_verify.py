"""01.파이썬 기본 문법 문서의 주장을 확인한다."""
import random


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    # 연산자 표
    check(7 * 2 == 14 and 7 / 2 == 3.5 and 7 // 2 == 3 and 7 % 2 == 1 and 2 ** 10 == 1024, "연산자 표")
    check((1 <= 2 < 3) is True and (True and False) is False, "비교·논리")
    # // 와 % 의 짝 관계, 나누는 수가 양수이면 나머지는 0 이상
    rng = random.Random(1)
    for _ in range(10000):
        a = rng.randint(-10**6, 10**6)
        b = rng.choice([x for x in range(-50, 51) if x != 0])
        check(a == (a // b) * b + a % b, f"짝 관계 {a} {b}")
        if b > 0:
            check(0 <= a % b < b, f"나머지 범위 {a} {b}")
    check(-7 // 2 == -4 and -7 % 2 == 1, "-7 // 2")
    check(all((n % 2 == 0) == (n in range(-100, 101, 2)) for n in range(-100, 101)), "음수 짝수 판정")
    # range
    check(list(range(5)) == [0, 1, 2, 3, 4], "range(5)")
    check(list(range(1, 5)) == [1, 2, 3, 4], "range(1,5)")
    check(list(range(0, 10, 3)) == [0, 3, 6, 9], "range(0,10,3)")
    check(list(range(4, 0, -1)) == [4, 3, 2, 1], "range(4,0,-1)")
    # 예시 코드
    total = 0
    for x in [3, 1, 4]:
        total += x
    check(total == 8, "total")
    check(list(enumerate("ab")) == [(0, "a"), (1, "b")], "enumerate")
    check([a + b for a, b in zip([1, 2], [10, 20])] == [11, 22], "zip")
    n, steps = 27, 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    check(steps == 111, f"27의 단계 수 {steps}")

    def solution(num):
        if num % 2 == 0:
            return "Even"
        else:
            return "Odd"
    check(solution(3) == "Odd" and solution(4) == "Even" and solution(0) == "Even" and solution(-3) == "Odd", "짝수와 홀수")

    def area(w, h=1):
        return w * h
    check(area(3, 4) == 12 and area(3) == 3, "기본값")
    # 확인 문제 C1
    s = 0
    for i in range(1, 10, 2):
        if i % 3 == 0:
            continue
        s += i
    check(s == 13, "C1")
    # C3: range(n)으로 1..n을 더하면 n=1에서 틀린다
    def wrong(n):
        t = 0
        for i in range(n):
            t += i
        return t
    first = next(n for n in range(1, 10) if wrong(n) != n * (n + 1) // 2)
    check(first == 1, "C3")
    check(isinstance(10 ** 20, int) and 10 ** 20 + 1 > 10 ** 20, "int 크기 제한 없음")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
