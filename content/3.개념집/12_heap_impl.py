"""12.힙과 우선순위 큐: 직접 만든 최소 힙과 heapq를 비교하고 문서의 주장을 확인한다."""
import heapq
import random


class MinHeap:
    """리스트 a에서 a[i] <= a[2i+1], a[i] <= a[2i+2]를 지키는 최소 힙."""

    def __init__(self):
        self.a = []

    def push(self, x):
        a = self.a
        a.append(x)
        i = len(a) - 1
        while i > 0:                          # 위로 올리기
            p = (i - 1) // 2
            if a[p] <= a[i]:
                break
            a[p], a[i] = a[i], a[p]
            i = p

    def pop(self):
        a = self.a
        top = a[0]
        last = a.pop()
        if a:
            a[0] = last
            i, n = 0, len(a)
            while True:                       # 아래로 내리기
                l, r, m = 2 * i + 1, 2 * i + 2, i
                if l < n and a[l] < a[m]:
                    m = l
                if r < n and a[r] < a[m]:
                    m = r
                if m == i:
                    break
                a[i], a[m] = a[m], a[i]
                i = m
        return top

    def ok(self):
        a = self.a
        return all(a[(i - 1) // 2] <= a[i] for i in range(1, len(a)))


if __name__ == "__main__":
    # 예시로 보기: 5, 3, 8, 1을 넣고 하나 꺼낸다
    h, states = [], []
    for x in (5, 3, 8, 1):
        heapq.heappush(h, x)
        states.append(h[:])
    assert states == [[5], [3, 5], [3, 5, 8], [1, 3, 8, 5]]
    assert heapq.heappop(h) == 1 and h == [3, 5, 8]
    mine = MinHeap()
    for x in (5, 3, 8, 1):
        mine.push(x)
    assert mine.a == [1, 3, 8, 5] and mine.pop() == 1 and mine.a == [3, 5, 8]
    # C1: 4, 7, 2, 9, 1을 넣은 뒤의 리스트와 두 번 꺼낸 값
    c = []
    for x in (4, 7, 2, 9, 1):
        heapq.heappush(c, x)
    assert c == [1, 2, 4, 9, 7]
    assert [heapq.heappop(c), heapq.heappop(c)] == [1, 2] and c == [4, 7, 9]
    # 최대 힙은 부호를 뒤집는다, 튜플은 앞 칸부터 비교한다
    mx = []
    for x in (5, 3, 8, 1):
        heapq.heappush(mx, -x)
    assert -heapq.heappop(mx) == 8
    t = []
    for item in [(3, "c"), (1, "b"), (1, "a"), (2, "z")]:
        heapq.heappush(t, item)
    assert [heapq.heappop(t) for _ in range(4)] == [(1, "a"), (1, "b"), (2, "z"), (3, "c")]
    try:                                      # 비교할 수 없는 둘째 칸
        bad = []
        heapq.heappush(bad, (1, {"a": 1}))
        heapq.heappush(bad, (1, {"b": 2}))
        raise AssertionError("TypeError가 나야 한다")
    except TypeError:
        pass
    ok3 = []
    heapq.heappush(ok3, (1, 0, {"a": 1}))
    heapq.heappush(ok3, (1, 1, {"b": 2}))
    assert heapq.heappop(ok3)[2] == {"a": 1}
    # heapify는 리스트를 제자리에서 힙으로 바꾼다
    a = [9, 4, 7, 1, 8, 2]
    heapq.heapify(a)
    assert a[0] == 1 and all(a[(i - 1) // 2] <= a[i] for i in range(1, len(a)))
    # 무작위: 직접 만든 힙과 heapq가 같은 순서로 꺼내고, 불변식이 늘 지켜진다
    rng = random.Random(12)
    for _ in range(2000):
        mine, ref = MinHeap(), []
        for _ in range(rng.randint(1, 40)):
            if ref and rng.random() < 0.4:
                assert mine.pop() == heapq.heappop(ref)
            else:
                x = rng.randint(-50, 50)
                mine.push(x)
                heapq.heappush(ref, x)
            assert mine.ok() and sorted(mine.a) == sorted(ref)
    # 높이: 원소 n개인 힙의 높이는 floor(log2 n), 100만 개면 19
    for n in range(1, 1001):                  # 칸 i의 깊이는 floor(log2(i + 1))
        assert max((i + 1).bit_length() - 1 for i in range(n)) == n.bit_length() - 1
    assert 2 ** 19 <= 1_000_000 < 2 ** 20
    print("ALL CHECKS PASSED")
