"""11.큐와 덱: 덱으로 큐와 LRU를 만들고 문서의 주장을 확인한다."""
import random
import time
from collections import OrderedDict, deque


def lru_deque(k, requests):
    cache, hits = deque(), []
    for x in requests:
        if x in cache:
            cache.remove(x)
            cache.append(x)
            hits.append(True)
        else:
            hits.append(False)
            if k == 0:
                continue
            if len(cache) == k:
                cache.popleft()
            cache.append(x)
    return hits, list(cache)


def lru_ordered(k, requests):
    cache, hits = OrderedDict(), []
    for x in requests:
        if x in cache:
            cache.move_to_end(x)
            hits.append(True)
        else:
            hits.append(False)
            if k == 0:
                continue
            if len(cache) == k:
                cache.popitem(last=False)
            cache[x] = True
    return hits, list(cache)


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    q, states, out = deque(), [], []
    for op in ["A", "B", None, "C", None]:
        if op is None:
            out.append(q.popleft())
        else:
            q.append(op)
        states.append("".join(q))
    check(states == ["A", "AB", "B", "BC", "C"] and out == ["A", "B"], "예시 표")
    d = deque([1, 2, 3])
    d.appendleft(0)
    d.append(4)
    check(list(d) == [0, 1, 2, 3, 4] and d[0] == 0 and d[-1] == 4 and d[2] == 2, "넣기, 보기")
    d.rotate(2)
    check(list(d) == [3, 4, 0, 1, 2], "rotate")
    m = deque(maxlen=2)
    for x in [1, 2, 3]:
        m.append(x)
    check(list(m) == [2, 3], "maxlen")
    z = deque(maxlen=0)
    z.append(1)
    check(len(z) == 0, "maxlen=0")
    # C1
    q = deque([1, 2, 3])
    q.append(4); q.popleft(); q.appendleft(0); q.rotate(1)
    check(list(q) == [4, 0, 2, 3], "C1")
    # C3
    check(lru_deque(2, list("ABAC"))[1] == ["A", "C"], "C3 LRU")
    fifo = deque(maxlen=2)
    for x in "ABAC":
        if x not in fifo:
            fifo.append(x)
    check(sorted(fifo) == ["B", "C"], "C3 FIFO")
    # 덱 LRU = OrderedDict LRU
    rng = random.Random(11)
    for _ in range(3000):
        k = rng.randint(0, 4)
        reqs = [rng.choice("ABCDEF") for _ in range(rng.randint(1, 20))]
        check(lru_deque(k, reqs) == lru_ordered(k, reqs), (k, reqs))
    # popleft vs pop(0)
    n = 100_000
    a = list(range(n))
    t = time.perf_counter()
    while a:
        a.pop(0)
    t_list = time.perf_counter() - t
    b = deque(range(n))
    t = time.perf_counter()
    while b:
        b.popleft()
    t_deque = time.perf_counter() - t
    print(f"list.pop(0) {t_list:.3f}초, deque.popleft {t_deque:.4f}초, {t_list / t_deque:.0f}배")
    check(t_list > 10 * t_deque, "popleft가 훨씬 빨라야 한다")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
