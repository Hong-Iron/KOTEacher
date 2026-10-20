"""14.트라이: 딕셔너리 노드로 만든 트라이와 문서 주장의 확인."""
import random


class Trie:
    def __init__(self):
        self.root = {"cnt": 0, "end": False, "kids": {}}

    def insert(self, word):
        node = self.root
        node["cnt"] += 1
        for ch in word:
            if ch not in node["kids"]:
                node["kids"][ch] = {"cnt": 0, "end": False, "kids": {}}
            node = node["kids"][ch]
            node["cnt"] += 1                 # 이 노드를 지나는 단어 수
        node["end"] = True

    def _walk(self, s):
        node = self.root
        for ch in s:
            node = node["kids"].get(ch)
            if node is None:
                return None
        return node

    def contains(self, word):
        node = self._walk(word)
        return node is not None and node["end"]

    def count_prefix(self, prefix):
        node = self._walk(prefix)
        return 0 if node is None else node["cnt"]

    def node_count(self):
        stack, n = [self.root], 0
        while stack:
            x = stack.pop()
            n += 1
            stack.extend(x["kids"].values())
        return n


if __name__ == "__main__":
    t = Trie()
    for w in ["go", "gone", "guild"]:
        t.insert(w)
    # 예시로 보기: 지나는 단어 수
    assert [t.count_prefix(p) for p in ("", "g", "go", "gon", "gu")] == [3, 3, 2, 1, 1]
    assert t.contains("go") and not t.contains("gon") and t.contains("gone")
    assert t.node_count() == 1 + 1 + 1 + 2 + 4          # 뿌리, g, o, n·e, u·i·l·d
    # C1: car, cat, cart, dog
    c = Trie()
    for w in ["car", "cat", "cart", "dog"]:
        c.insert(w)
    assert (c.count_prefix("ca"), c.count_prefix("car"), c.count_prefix("d")) == (3, 2, 1)
    assert c.node_count() == 1 + 3 + 1 + 1 + 3               # 뿌리, c-a-r, t(cat), t(cart), d-o-g
    # 무작위: 집합과 앞부분 세기를 직접 한 결과와 비교
    rng = random.Random(14)
    for _ in range(1500):
        words = list({"".join(rng.choice("abc") for _ in range(rng.randint(1, 5))) for _ in range(rng.randint(1, 20))})
        tr = Trie()
        for w in words:
            tr.insert(w)
        for _ in range(10):
            q = "".join(rng.choice("abc") for _ in range(rng.randint(0, 5)))
            assert tr.contains(q) == (q in set(words))
            assert tr.count_prefix(q) == sum(1 for w in words if w.startswith(q))
    print("ALL CHECKS PASSED")
