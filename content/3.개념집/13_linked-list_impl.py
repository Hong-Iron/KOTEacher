"""13.연결 리스트: 배열 두 개(prev, next)로 만든 이중 연결 리스트와 문서 주장의 확인."""
import bisect
import random
import time


class Rows:
    """0 ~ n-1번 칸을 앞뒤로 이은 줄. 앞 이웃이 없으면 -1, 뒤 이웃이 없으면 n."""

    def __init__(self, n):
        self.n = n
        self.prev = [i - 1 for i in range(n)]
        self.next = [i + 1 for i in range(n)]
        self.alive = [True] * n
        self.removed = []                 # 지운 순서를 쌓는 스택

    def remove(self, x):
        p, q = self.prev[x], self.next[x]
        if p != -1:
            self.next[p] = q
        if q != self.n:
            self.prev[q] = p
        self.alive[x] = False
        self.removed.append(x)            # x의 prev, next는 그대로 둔다

    def restore(self):
        x = self.removed.pop()            # 가장 최근에 지운 것
        p, q = self.prev[x], self.next[x]
        if p != -1:
            self.next[p] = x
        if q != self.n:
            self.prev[q] = x
        self.alive[x] = True
        return x

    def walk(self):
        start = next((i for i in range(self.n) if self.alive[i] and self.prev[i] == -1), None)
        out, x = [], start
        while x is not None and x != self.n:
            out.append(x)
            x = self.next[x]
        return out

    def invariant(self):
        for x in range(self.n):
            if self.alive[x]:
                p, q = self.prev[x], self.next[x]
                if p != -1 and (self.next[p] != x or not self.alive[p]):
                    return False
                if q != self.n and (self.prev[q] != x or not self.alive[q]):
                    return False
        return True


def walk_from0(r, limit=50):
    out, x = [], 0
    while x != r.n and len(out) < limit:
        out.append(x)
        x = r.next[x]
    return out


if __name__ == "__main__":
    # 예시로 보기의 표: 5칸에서 2, 3을 지우고 3, 2 순서로 되살린다
    r = Rows(5)
    assert (r.prev, r.next) == ([-1, 0, 1, 2, 3], [1, 2, 3, 4, 5])
    r.remove(2)
    assert (r.next[1], r.prev[3], r.prev[2], r.next[2]) == (3, 1, 1, 3) and r.walk() == [0, 1, 3, 4]
    r.remove(3)
    assert (r.next[1], r.prev[4], r.prev[3], r.next[3]) == (4, 1, 1, 4) and r.walk() == [0, 1, 4]
    assert r.restore() == 3 and (r.next[1], r.prev[4]) == (3, 3) and r.walk() == [0, 1, 3, 4]
    assert r.restore() == 2 and (r.prev, r.next) == ([-1, 0, 1, 2, 3], [1, 2, 3, 4, 5])
    # 순서를 어기면: 2, 3을 지운 뒤 2부터 되살리면 죽은 3이 줄에 끼어든다
    w = Rows(5)
    w.remove(2)
    w.remove(3)
    p, q = w.prev[2], w.next[2]           # 1, 3
    w.next[p], w.prev[q] = 2, 2
    assert walk_from0(w) == [0, 1, 2, 3, 4] and not w.alive[3]
    # C1: 6칸에서 2, 3을 지우고 한 번 되살린다
    c = Rows(6)
    c.remove(2)
    c.remove(3)
    assert c.restore() == 3 and c.next[1] == 3 and c.walk() == [0, 1, 3, 4, 5]
    # 무작위: 파이썬 리스트로 흉내 낸 결과와 비교, 불변식 확인
    rng = random.Random(13)
    for _ in range(3000):
        n = rng.randint(1, 12)
        r, alive = Rows(n), list(range(n))
        for _ in range(rng.randint(1, 30)):
            if r.removed and (len(alive) <= 1 or rng.random() < 0.4):
                x = r.restore()
                bisect.insort(alive, x)
            elif len(alive) > 1:
                x = rng.choice(alive)
                r.remove(x)
                alive.remove(x)
            assert r.walk() == alive and r.invariant()
    # 가운데 지우기 비용: 20만 칸에서 가운데 근처를 5만 번 지운다
    n, m = 200_000, 50_000
    a = list(range(n))
    t0 = time.perf_counter()
    for _ in range(m):
        del a[len(a) // 2]
    t_list = time.perf_counter() - t0
    r = Rows(n)
    x = n // 2
    t0 = time.perf_counter()
    for _ in range(m):
        nx = r.next[x]
        r.remove(x)
        x = nx
    t_link = time.perf_counter() - t0
    assert t_list > 30 * t_link, (t_list, t_link)
    print(f"list del {t_list:.3f}s, linked remove {t_link:.3f}s, ratio {t_list / t_link:.0f}")
    print("ALL CHECKS PASSED")
