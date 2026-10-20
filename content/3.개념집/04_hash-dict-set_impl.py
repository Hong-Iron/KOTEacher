"""04.딕셔너리와 집합: 해시 테이블을 직접 만들어 보고, 문서의 주장을 확인한다.

TinyDict는 설명용 구현이다. 칸마다 (키, 값) 목록을 매달고(chaining),
칸 하나당 평균 키 수가 1을 넘으면 칸 수를 두 배로 늘려 모두 다시 넣는다.
"""
import random
from collections import Counter, defaultdict


class TinyDict:
    def __init__(self):
        self.m = 8                                  # 칸 수
        self.n = 0                                  # 들어 있는 키 수
        self.slots = [[] for _ in range(self.m)]

    def _slot(self, key):
        return self.slots[hash(key) % self.m]       # 해시 → 나머지 → 칸

    def put(self, key, value):
        slot = self._slot(key)
        for i, (k, _) in enumerate(slot):
            if k == key:                            # 같은 키는 하나만: 값만 바꾼다
                slot[i] = (key, value)
                return
        slot.append((key, value))
        self.n += 1
        if self.n > self.m:                         # 너무 차면 두 배로 늘린다
            self._grow()

    def get(self, key, default=None):
        for k, v in self._slot(key):
            if k == key:
                return v
        return default

    def delete(self, key):
        slot = self._slot(key)
        for i, (k, _) in enumerate(slot):
            if k == key:
                slot.pop(i)
                self.n -= 1
                return True
        return False

    def _grow(self):
        items = [kv for slot in self.slots for kv in slot]
        self.m *= 2
        self.slots = [[] for _ in range(self.m)]
        for k, v in items:
            self._slot(k).append((k, v))

    def avg_chain(self):
        used = [len(s) for s in self.slots if s]
        return sum(used) / len(used) if used else 0.0


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    # 1. TinyDict가 dict와 같게 동작하는지 무작위 비교
    rng = random.Random(4)
    mine, ref = TinyDict(), {}
    for _ in range(20000):
        k = rng.randrange(3000) if rng.random() < 0.7 else f"s{rng.randrange(500)}"
        op = rng.random()
        if op < 0.5:
            v = rng.randrange(10**6)
            mine.put(k, v)
            ref[k] = v
        elif op < 0.8:
            check(mine.get(k) == ref.get(k), "get 불일치")
        else:
            check(mine.delete(k) == (k in ref), "delete 불일치")
            ref.pop(k, None)
        check(mine.n == len(ref), "개수 불일치")
    print(f"TinyDict: 키 {mine.n}개, 칸 {mine.m}개, 쓰는 칸의 평균 키 수 {mine.avg_chain():.2f}")
    check(mine.avg_chain() < 2.0, "칸마다 평균 키 수가 작아야 한다")

    # 2. 예시: 과일 세기
    fruits = ["사과", "배", "사과", "귤", "사과"]
    count = {}
    for f in fruits:
        count[f] = count.get(f, 0) + 1
    check(count == {"사과": 3, "배": 1, "귤": 1} and list(count) == ["사과", "배", "귤"], "과일 세기와 순서")

    # 3. 표의 동작
    d = {"a": 1}
    d["a"] = 5
    check(d == {"a": 5}, "같은 키는 값만 바뀐다")
    try:
        d["없음"]
        check(False, "KeyError가 나야 한다")
    except KeyError:
        pass
    check(d.get("없음", 0) == 0 and ("a" in d) and (5 in d.values()), "get, in")
    s = {1, 2}
    t = {2, 3}
    check(s | t == {1, 2, 3} and s & t == {2} and s - t == {1}, "집합 연산")
    s.discard(99)
    check(s == {1, 2} and type({}) is dict and set() == set(), "discard, 빈 집합")
    check(sorted(set([3, 1, 3, 2, 1])) == [1, 2, 3], "중복 없애기")
    try:
        {[1, 2]: "x"}
        check(False, "리스트 키는 TypeError")
    except TypeError:
        pass
    check({(1, 2): "x"}[(1, 2)] == "x", "튜플 키")

    # 4. Counter, defaultdict
    c = Counter(["사과", "배", "사과"])
    check(c == {"사과": 2, "배": 1} and c["없는것"] == 0 and c.most_common(1) == [("사과", 2)], "Counter")
    check(Counter("aab") - Counter("ab") == Counter({"a": 1}), "Counter 빼기")
    g = defaultdict(list)
    g["과일"].append("사과")
    check(dict(g) == {"과일": ["사과"]}, "defaultdict")

    # 5. 스스로 설명해 보기 코드, 같은 개수면 먼저 넣은 단어
    def most_frequent(words):
        cnt = {}
        for w in words:
            cnt[w] = cnt.get(w, 0) + 1
        return max(cnt, key=cnt.get)
    check(most_frequent(["b", "a", "b", "a", "c"]) == "b", "같은 개수면 먼저 넣은 것")
    check(most_frequent(["x", "y", "y"]) == "y", "가장 많은 것")

    # 6. 확인 문제 C1
    d = {}
    for ch in "banana":
        d[ch] = d.get(ch, 0) + 1
    check(list(d.items()) == [("b", 1), ("a", 3), ("n", 2)], "C1")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
