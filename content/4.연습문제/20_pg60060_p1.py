"""가사 검색 (프로그래머스 60060) 풀이와 검증."""
import random
import time
from bisect import bisect_left, bisect_right
from collections import defaultdict


def solution(words, queries):
    fwd, rev = defaultdict(list), defaultdict(list)       # 길이별로 모은다
    for w in words:
        fwd[len(w)].append(w)
        rev[len(w)].append(w[::-1])
    for L in fwd:
        fwd[L].sort()
        rev[L].sort()
    answer = []
    for q in queries:
        if q[0] == "?":                                   # 앞이 ?면 뒤집어서 뒤쪽 ?로 만든다
            arr, q = rev[len(q)], q[::-1]
        else:
            arr = fwd[len(q)]
        lo = q.replace("?", "a")                          # 이 범위 안의 단어가 모두 맞는다
        hi = q.replace("?", "z")
        answer.append(bisect_right(arr, hi) - bisect_left(arr, lo))
    return answer


def by_matching(words, queries):
    out = []
    for q in queries:
        out.append(sum(1 for w in words if len(w) == len(q) and all(a == "?" or a == b for a, b in zip(q, w))))
    return out


if __name__ == "__main__":
    words = ["frodo", "front", "frost", "frozen", "frame", "kakao"]
    queries = ["fro??", "????o", "fr???", "fro???", "pro?"]
    assert solution(words, queries) == [3, 2, 4, 1, 0] == by_matching(words, queries)
    # 6단계 추적: 길이 5 단어의 정렬 목록과 범위
    five = sorted(w for w in words if len(w) == 5)
    assert five == ["frame", "frodo", "front", "frost", "kakao"]
    assert (bisect_left(five, "froaa"), bisect_right(five, "frozz")) == (1, 4)
    rfive = sorted(w[::-1] for w in words if len(w) == 5)
    assert rfive == ["emarf", "oakak", "odorf", "tnorf", "tsorf"]
    assert (bisect_left(rfive, "oaaaa"), bisect_right(rfive, "ozzzz")) == (1, 3)
    assert (bisect_left(five, "fraaa"), bisect_right(five, "frzzz")) == (0, 4)
    assert (bisect_left(["frozen"], "froaaa"), bisect_right(["frozen"], "frozzz")) == (0, 1)
    assert "froaa" < "froz" < "frozz"                          # 길이를 나누지 않으면 섞여 들어온다
    assert chr(ord("z") + 1) == "{" and bisect_left(five, "fro{{") - bisect_left(five, "froaa") == 3
    # 무작위: 알파벳 a, b, c만 쓰는 짧은 단어
    rng = random.Random(60060)
    for _ in range(1500):
        ws = list({"".join(rng.choice("abc") for _ in range(rng.randint(1, 4))) for _ in range(rng.randint(2, 15))})
        qs = []
        for _ in range(rng.randint(2, 10)):
            L = rng.randint(1, 4)
            k = rng.randint(1, L)
            body = "".join(rng.choice("abc") for _ in range(L - k))
            qs.append("?" * k + body if rng.random() < 0.5 else body + "?" * k)
        assert solution(ws, qs) == by_matching(ws, qs), (ws, qs)
    # 효율성: 단어 10만 개, 키워드 10만 개(길이 합 각 100만 이하)
    ws = list({"".join(rng.choice("abcdefghij") for _ in range(rng.randint(5, 10))) for _ in range(100_000)})
    qs = []
    for _ in range(100_000):
        L = rng.randint(5, 10)
        k = rng.randint(1, L)
        body = "".join(rng.choice("abcdefghij") for _ in range(L - k))
        qs.append("?" * k + body if rng.random() < 0.5 else body + "?" * k)
    t0 = time.perf_counter()
    solution(ws, qs)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"100k words, 100k queries: {t:.2f}s")
    print("ALL CHECKS PASSED")
