"""비밀지도 (프로그래머스 17681) 풀이와 검증."""
import random


def solution(n, arr1, arr2):
    answer = []
    for a, b in zip(arr1, arr2):
        bits = format(a | b, f"0{n}b")
        answer.append(bits.replace("1", "#").replace("0", " "))
    return answer


def by_cells(n, arr1, arr2):
    """숫자를 2로 나누며 칸을 하나씩 구한다(오른쪽 칸부터)."""
    out = []
    for a, b in zip(arr1, arr2):
        row = []
        for _ in range(n):
            wall = a % 2 == 1 or b % 2 == 1
            row.append("#" if wall else " ")
            a //= 2
            b //= 2
        out.append("".join(reversed(row)))
    return out


if __name__ == "__main__":
    assert solution(5, [9, 20, 28, 18, 11], [30, 1, 21, 17, 28]) == ["#####", "# # #", "### #", "#  ##", "#####"]
    assert solution(6, [46, 33, 33, 22, 31, 50], [27, 56, 19, 14, 14, 10]) == ["######", "###  #", "##  ##", " #### ", " #####", "### # "]
    assert solution(3, [5], [2]) == ["###"]
    assert bin(5) == "0b101" and bin(5)[2:].zfill(5) == format(5, "05b") == "00101"
    rng = random.Random(17681)
    for _ in range(2000):
        n = rng.randint(1, 16)
        arr1 = [rng.randrange(2 ** n) for _ in range(n)]
        arr2 = [rng.randrange(2 ** n) for _ in range(n)]
        assert solution(n, arr1, arr2) == by_cells(n, arr1, arr2)
    print("ALL CHECKS PASSED")
