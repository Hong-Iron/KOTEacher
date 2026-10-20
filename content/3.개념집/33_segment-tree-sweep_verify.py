"""세그먼트 트리와 스위핑: 문서의 예시 값, 확인 문제 답, 무작위 비교."""
import math
import random


class SegTree:
    """구간 합(또는 결합 법칙이 맞는 다른 연산)과 한 칸 바꾸기. 칸은 0부터, 구간은 [l, r)."""

    def __init__(self, a, op=lambda x, y: x + y, empty=0):
        self.op, self.empty = op, empty
        self.size = 1
        while self.size < len(a):
            self.size *= 2
        self.t = [empty] * (2 * self.size)
        self.t[self.size:self.size + len(a)] = a
        for i in range(self.size - 1, 0, -1):
            self.t[i] = op(self.t[2 * i], self.t[2 * i + 1])

    def update(self, i, value):
        i += self.size
        self.t[i] = value
        changed = [i]
        i //= 2
        while i:                               # 위로 올라가며 다시 계산한다
            self.t[i] = self.op(self.t[2 * i], self.t[2 * i + 1])
            changed.append(i)
            i //= 2
        return changed

    def query(self, l, r):
        res_l, res_r = self.empty, self.empty
        used = []
        l += self.size
        r += self.size
        while l < r:
            if l & 1:                          # l이 오른쪽 자식이면 그 마디를 통째로 쓴다
                res_l = self.op(res_l, self.t[l])
                used.append(l)
                l += 1
            if r & 1:
                r -= 1
                res_r = self.op(self.t[r], res_r)
                used.append(r)
            l //= 2
            r //= 2
        return self.op(res_l, res_r), used


def union_area(rects):
    """스위핑 + 덮인 길이 트리 (직사각형의 넓이 풀이와 같은 방법)."""
    ys = sorted({y for _, y1, _, y2 in rects for y in (y1, y2)})
    where = {y: i for i, y in enumerate(ys)}
    size = 1
    while size < len(ys) - 1:
        size *= 2
    length = [0] * (2 * size)
    for i in range(len(ys) - 1):
        length[size + i] = ys[i + 1] - ys[i]
    for i in range(size - 1, 0, -1):
        length[i] = length[2 * i] + length[2 * i + 1]
    cnt, cov = [0] * (2 * size), [0] * (2 * size)

    def pull(i):
        cov[i] = length[i] if cnt[i] else (0 if i >= size else cov[2 * i] + cov[2 * i + 1])

    def update(l, r, v):
        l += size
        r += size
        l0, r0 = l, r - 1
        while l < r:
            if l & 1:
                cnt[l] += v
                pull(l)
                l += 1
            if r & 1:
                r -= 1
                cnt[r] += v
                pull(r)
            l //= 2
            r //= 2
        for i in (l0 // 2, r0 // 2):
            while i:
                pull(i)
                i //= 2

    events = sorted([(x1, 1, where[y1], where[y2]) for x1, y1, _, y2 in rects] +
                    [(x2, -1, where[y1], where[y2]) for _, y1, x2, y2 in rects])
    area, prev = 0, events[0][0]
    for x, v, lo, hi in events:
        area += cov[1] * (x - prev)
        update(lo, hi, v)
        prev = x
    return area


def area_by_cells(rects):
    xs = sorted({x for x1, _, x2, _ in rects for x in (x1, x2)})
    ys = sorted({y for _, y1, _, y2 in rects for y in (y1, y2)})
    return sum((xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j])
               for i in range(len(xs) - 1) for j in range(len(ys) - 1)
               if any(x1 <= xs[i] < x2 and y1 <= ys[j] < y2 for x1, y1, x2, y2 in rects))


if __name__ == "__main__":
    a = [5, 3, 7, 2, 6, 1, 4, 8]
    st = SegTree(a)
    # 예시 그림의 마디 값 (1번이 뿌리, 2·3번이 그 아래, …)
    assert st.t[1:8] == [36, 17, 19, 8, 9, 7, 12]
    total, used = st.query(2, 7)               # 2 ~ 6번 칸
    assert total == 20 == sum(a[2:7]) and sorted(used) == [5, 6, 14]
    assert st.update(3, 9) == [11, 5, 2, 1] and st.t[1] == 43 and st.t[5] == 16 and st.t[2] == 24
    # 확인 문제 C1: 처음 배열에서 5번 칸을 1 → 10
    st2 = SegTree(a)
    st2.update(5, 10)
    assert (st2.t[13], st2.t[6], st2.t[3], st2.t[1]) == (10, 16, 28, 45)
    # 오해: 합이 아니어도 된다 (최솟값)
    rng = random.Random(33)
    for _ in range(300):
        n = rng.randint(1, 40)
        arr = [rng.randint(-50, 50) for _ in range(n)]
        s_sum, s_min = SegTree(arr), SegTree(arr, min, float("inf"))
        s_max, s_gcd = SegTree(arr, max, float("-inf")), SegTree(arr, math.gcd, 0)
        for _ in range(60):
            if rng.random() < 0.4:
                i, v = rng.randrange(n), rng.randint(-50, 50)
                arr[i] = v
                for tree in (s_sum, s_min, s_max, s_gcd):
                    tree.update(i, v)
            else:
                l = rng.randrange(n)
                r = rng.randint(l + 1, n)
                assert s_sum.query(l, r)[0] == sum(arr[l:r])
                assert s_min.query(l, r)[0] == min(arr[l:r])
                assert s_max.query(l, r)[0] == max(arr[l:r])
                assert s_gcd.query(l, r)[0] == math.gcd(*arr[l:r])
                assert len(s_sum.query(l, r)[1]) <= 2 * s_sum.size.bit_length()
    # 스위핑: 예시 두 직사각형과 무작위 비교
    assert union_area([[0, 1, 4, 4], [3, 1, 5, 3]]) == 14
    for _ in range(1000):
        rects = []
        for _ in range(rng.randint(1, 7)):
            x1, x2 = sorted(rng.sample(range(12), 2))
            y1, y2 = sorted(rng.sample(range(12), 2))
            rects.append([x1, y1, x2, y2])
        assert union_area(rects) == area_by_cells(rects), rects
    print("ALL CHECKS PASSED")
