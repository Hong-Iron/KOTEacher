"""성격 유형 검사하기 (프로그래머스 118666) 풀이와 검증."""
import random


def solution(survey, choices):
    score = {t: 0 for t in "RTCFJMAN"}
    for s, c in zip(survey, choices):
        if c < 4:
            score[s[0]] += 4 - c
        elif c > 4:
            score[s[1]] += c - 4
    answer = ""
    for a, b in ["RT", "CF", "JM", "AN"]:
        answer += a if score[a] >= score[b] else b
    return answer


def by_table(survey, choices):
    """1단계의 점수 표를 그대로 옮긴 풀이."""
    side = {1: 0, 2: 0, 3: 0, 4: None, 5: 1, 6: 1, 7: 1}
    pts = {1: 3, 2: 2, 3: 1, 4: 0, 5: 1, 6: 2, 7: 3}
    score = {}
    for s, c in zip(survey, choices):
        if side[c] is not None:
            t = s[side[c]]
            score[t] = score.get(t, 0) + pts[c]
    out = []
    for pair in ["RT", "CF", "JM", "AN"]:
        x, y = sorted(pair)
        out.append(x if score.get(x, 0) >= score.get(y, 0) else y)
    return "".join(out)


if __name__ == "__main__":
    assert solution(["AN", "CF", "MJ", "RT", "NA"], [5, 3, 2, 7, 5]) == "TCMA"
    assert solution(["TR", "RT", "TR"], [7, 1, 3]) == "RCJA"
    assert solution(["RT", "NA"], [7, 2]) == "TCJN"
    rng = random.Random(118666)
    kinds = ["RT", "TR", "FC", "CF", "MJ", "JM", "AN", "NA"]
    for _ in range(2000):
        n = rng.randint(1, 30)
        sv = [rng.choice(kinds) for _ in range(n)]
        ch = [rng.randint(1, 7) for _ in range(n)]
        assert solution(sv, ch) == by_table(sv, ch)
    print("ALL CHECKS PASSED")
