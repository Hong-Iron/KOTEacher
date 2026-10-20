"""후보키 (프로그래머스 42890) 풀이와 검증."""
import random
from itertools import combinations


def solution(relation):
    rows, cols = len(relation), len(relation[0])
    keys = []
    for size in range(1, cols + 1):
        for combo in combinations(range(cols), size):
            if any(set(k) <= set(combo) for k in keys):
                continue
            seen = {tuple(row[c] for c in combo) for row in relation}
            if len(seen) == rows:
                keys.append(combo)
    return len(keys)


def by_definition(relation):
    rows, cols = len(relation), len(relation[0])

    def unique(mask):
        return len({tuple(r[c] for c in range(cols) if mask >> c & 1) for r in relation}) == rows

    count = 0
    for mask in range(1, 1 << cols):
        if not unique(mask):
            continue
        minimal = all(not unique(mask & ~(1 << c)) for c in range(cols) if mask >> c & 1 and mask & ~(1 << c))
        if minimal:
            count += 1
    return count


if __name__ == "__main__":
    ex = [["100", "ryan", "music", "2"], ["200", "apeach", "math", "2"], ["300", "tube", "computer", "3"],
          ["400", "con", "computer", "4"], ["500", "muzi", "music", "3"], ["600", "apeach", "music", "2"]]
    assert solution(ex) == 2 == by_definition(ex)
    small = [["1", "kim", "A"], ["2", "lee", "A"], ["3", "kim", "B"]]
    assert solution(small) == 2
    # 6단계 표: 크기 1에서 학번만 유일, 크기 2에서 (이름, 전공)이 유일
    uniq = lambda cols: len({tuple(r[c] for c in cols) for r in ex}) == len(ex)
    assert [uniq((c,)) for c in range(4)] == [True, False, False, False]
    assert uniq((1, 2)) and not uniq((1, 3)) and not uniq((2, 3))
    rng = random.Random(42890)
    for _ in range(2000):
        cols, rows = rng.randint(1, 5), rng.randint(1, 8)
        rel = set()
        while len(rel) < rows:
            rel.add(tuple(rng.choice("ab") if rng.random() < 0.7 else rng.choice("abcd") for _ in range(cols)))
            if len(rel) < rows and len(rel) >= 4 ** cols:
                break
        rel = [list(r) for r in rel]
        assert solution(rel) == by_definition(rel), rel
    print("ALL CHECKS PASSED")
