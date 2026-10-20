"""[3차] 자동완성 (프로그래머스 17685) 풀이와 검증."""
import random
import time


def solution(words):
    root = {}
    for w in words:                          # 트라이에 넣으며 칸마다 지나는 단어 수를 센다
        node = root
        for ch in w:
            if ch not in node:
                node[ch] = [0, {}]           # [지나는 단어 수, 자식들]
            node[ch][0] += 1
            node = node[ch][1]
    total = 0
    for w in words:
        node = root
        typed = len(w)                       # 끝까지 쳐야 하는 경우가 기본
        for i, ch in enumerate(w):
            cnt, kids = node[ch]
            if cnt == 1:                     # 이 앞부분을 가진 단어가 나 하나뿐
                typed = i + 1
                break
            node = kids
        total += typed
    return total


def by_lcp(words):
    """단어마다 다른 단어와의 가장 긴 공통 앞부분 + 1(단어 길이를 넘지 않게)."""
    def lcp(a, b):
        k = 0
        while k < len(a) and k < len(b) and a[k] == b[k]:
            k += 1
        return k
    total = 0
    for i, w in enumerate(words):
        m = max((lcp(w, x) for j, x in enumerate(words) if j != i), default=0)
        total += min(len(w), m + 1)
    return total


def by_sorted_neighbors(words):
    """정렬하면 공통 앞부분이 가장 긴 상대는 바로 앞이나 뒤 단어다."""
    def lcp(a, b):
        k = 0
        while k < len(a) and k < len(b) and a[k] == b[k]:
            k += 1
        return k
    ws = sorted(words)
    total = 0
    for i, w in enumerate(ws):
        m = 0
        if i > 0:
            m = max(m, lcp(w, ws[i - 1]))
        if i + 1 < len(ws):
            m = max(m, lcp(w, ws[i + 1]))
        total += min(len(w), m + 1)
    return total


def typed_each(words):
    root = {}
    for w in words:
        node = root
        for ch in w:
            if ch not in node:
                node[ch] = [0, {}]
            node[ch][0] += 1
            node = node[ch][1]
    out = []
    for w in words:
        node, typed = root, len(w)
        for i, ch in enumerate(w):
            cnt, kids = node[ch]
            if cnt == 1:
                typed = i + 1
                break
            node = kids
        out.append(typed)
    return out


if __name__ == "__main__":
    assert solution(["go", "gone", "guild"]) == 7 == by_lcp(["go", "gone", "guild"])
    assert solution(["abc", "def", "ghi", "jklm"]) == 4
    assert solution(["word", "war", "warrior", "world"]) == 15
    assert typed_each(["word", "war", "warrior", "world"]) == [4, 3, 4, 4]
    rng = random.Random(17685)
    for _ in range(2000):
        ws = list({"".join(rng.choice("ab") for _ in range(rng.randint(1, 6))) for _ in range(rng.randint(2, 12))})
        if len(ws) < 2:
            continue
        assert solution(ws) == by_lcp(ws) == by_sorted_neighbors(ws), ws
    # 단어 10만 개, 길이 합 100만
    ws = list({"".join(rng.choice("abcde") for _ in range(10)) for _ in range(100_000)})
    t0 = time.perf_counter()
    solution(ws)
    t = time.perf_counter() - t0
    assert t < 10, t
    print(f"{len(ws)} words: {t:.2f}s")
    print("ALL CHECKS PASSED")
