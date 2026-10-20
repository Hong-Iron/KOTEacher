"""압축 (프로그래머스 17684) 풀이와 검증."""
import random


def solution(msg):
    dic = {chr(ord("A") + i): i + 1 for i in range(26)}
    answer = []
    i = 0
    while i < len(msg):
        j = i + 1
        while j < len(msg) and msg[i:j + 1] in dic:
            j += 1
        w = msg[i:j]
        answer.append(dic[w])
        if j < len(msg):
            dic[msg[i:j + 1]] = len(dic) + 1
        i = j
    return answer


def decode(codes):
    """LZW 복원. 색인 → 문자열 사전을 압축과 같은 순서로 다시 만든다."""
    dic = {i + 1: chr(ord("A") + i) for i in range(26)}
    w = dic[codes[0]]
    out = [w]
    for k in codes[1:]:
        entry = dic[k] if k in dic else w + w[0]
        out.append(entry)
        dic[len(dic) + 1] = w + entry[0]
        w = entry
    return "".join(out)


if __name__ == "__main__":
    assert solution("KAKAO") == [11, 1, 27, 15]
    assert solution("TOBEORNOTTOBEORTOBEORNOT") == [20, 15, 2, 5, 15, 18, 14, 15, 20, 27, 29, 31, 36, 30, 32, 34]
    assert solution("ABABABABABABABAB") == [1, 2, 27, 29, 28, 31, 30]
    assert solution("ABAB") == [1, 2, 27]
    rng = random.Random(17684)
    for _ in range(3000):
        s = "".join(rng.choice("ABC" if rng.random() < 0.5 else "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                    for _ in range(rng.randint(1, 60)))
        assert decode(solution(s)) == s, s
    print("ALL CHECKS PASSED")
