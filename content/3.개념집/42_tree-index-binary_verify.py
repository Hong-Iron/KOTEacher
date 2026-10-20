"""트리 칸 번호 ↔ 2진법 자릿수: 문서의 모든 수치와 주장을 계산으로 확인한다.

번호 규칙: 뿌리 1, 칸 i의 자식 2i(왼쪽), 2i + 1(오른쪽). heapq는 0-based라 칸 j가 번호 j + 1이다.
세그먼트 트리는 33 문서의 아래에서 위로 만드는 판(잎 size + i, 묻기는 [l, r))을 따른다.
표준 라이브러리만 쓴다. 실험 통과는 증명이 아니다. 작은 범위 전수와 무작위 입력으로 확인한다.
"""
import heapq
import ipaddress
import random

random.seed(42)


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def bits(i):
    return bin(i)[2:]


def ancestors(i):
    """i에서 뿌리까지의 번호 목록(i 포함)."""
    out = [i]
    while i > 1:
        i //= 2
        out.append(i)
    return out


def depth_walk(i):
    """// 2를 몇 번 해야 뿌리에 닿는가."""
    d = 0
    while i > 1:
        i //= 2
        d += 1
    return d


def floor_lg(n):
    """정수만으로 구한 floor(log2 n), n >= 1."""
    k = 0
    while (1 << (k + 1)) <= n:
        k += 1
    return k


def ceil_lg(n):
    """정수만으로 구한 ceil(log2 n), n >= 1."""
    k = 0
    while (1 << k) < n:
        k += 1
    return k


def walk(path_bits):
    """뿌리 1에서 길(0 = 왼쪽, 1 = 오른쪽)을 따라 내려간 칸 번호와 지나간 칸 목록."""
    i, seen = 1, [1]
    for b in path_bits:
        i = 2 * i + int(b)
        seen.append(i)
    return i, seen


def lca_brute(a, b):
    sa = set(ancestors(a))
    for x in ancestors(b):
        if x in sa:
            return x
    raise AssertionError("공통 조상 없음")


def lcp(s, t):
    k = 0
    while k < min(len(s), len(t)) and s[k] == t[k]:
        k += 1
    return s[:k]


def lca(a, b):
    """문서의 비트 연산 코드."""
    da, db = a.bit_length(), b.bit_length()
    if da > db:
        a >>= da - db
    else:
        b >>= db - da
    return a >> (a ^ b).bit_length()


def node_range(v, size):
    """size(2의 거듭제곱) 세그먼트 트리에서 마디 v가 맡은 칸 [lo, hi)."""
    d = v.bit_length() - 1
    K = size.bit_length() - 1
    w = 1 << (K - d)
    pos = v - (1 << d)
    return pos * w, (pos + 1) * w


# ------------------------------------------------ 비교 표: 13번 칸
check(bits(13) == "1101", "13 = 1101")
check((2 * 13, 2 * 13 + 1) == (26, 27), "13의 자식 26, 27")
check(bits(26) == "11010" and bits(27) == "11011", "끝에 0, 1을 붙인 수")
check(ancestors(13) == [13, 6, 3, 1], "13 → 6 → 3 → 1")
check([divmod(x, 2) for x in (13, 6, 3)] == [(6, 1), (3, 0), (1, 1)], "반복 나눗셈 13 = 2·6 + 1, 6 = 2·3 + 0, 3 = 2·1 + 1")
end, seen = walk(bits(13)[1:])
check(end == 13 and seen == [1, 3, 6, 13], "뿌리에서 오른쪽(3), 왼쪽(6), 오른쪽(13)")
check(bits(13)[1:] == "101", "맨 앞 1 뒤의 자리 1, 0, 1")
check(depth_walk(13) == 3 == floor_lg(13) == 13 .bit_length() - 1, "13의 깊이 3 = floor(lg 13)")
check(len(bits(13)) == 4, "13은 4자리")
levels13 = max(depth_walk(i) for i in range(1, 14)) + 1
check(levels13 == 4, "칸 13개 힙은 4층")
check([i for i in range(1, 14) if depth_walk(i) == 3] == list(range(8, 14)), "맨 아래 층은 8 ~ 13번")
check([n for n in range(1, 100) if len(bits(n)) == 4] == list(range(8, 16)), "4자리 2진수는 8 ~ 15")
check(int("1000", 2) == 8 and int("1111", 2) == 15, "1000₂ = 8, 1111₂ = 15")
check(lca_brute(13, 7) == 3 and lcp(bits(13), bits(7)) == "11" and int("11", 2) == 3, "13과 7의 공통 조상 3 = 공통 앞부분 11₂")
check(13 // 2 == 6 and 6 // 2 == 3 and 7 // 2 == 3, "13을 한 층 올리면 6, 6과 7의 부모 3")
check(8 + 5 == 13 and bits(13) == "1" + format(5, "03b"), "size 8 세그먼트 트리에서 5번 칸의 잎 13 = 1 + 101")
check(13 - 1 == 12, "heapq로는 h[12]")

# ------------------------------------------------ heapq의 0-based 식과 실제 heapq
for j in range(0, 5000):
    i = j + 1
    check(2 * j + 1 + 1 == 2 * i and 2 * j + 2 + 1 == 2 * i + 1, f"heapq 자식 +1 = 2i, 2i + 1 ({j})")
    if j >= 1:
        check((j - 1) // 2 + 1 == i // 2, f"heapq 부모 +1 = i // 2 ({j})")
    check(2 * (j + 1) - 1 == 2 * j + 1 and 2 * (j + 1) + 1 - 1 == 2 * j + 2, "1 더하고 붙이고 1 빼기")
    check((j + 1) // 2 - 1 == (j - 1) // 2, "(j + 1) // 2 - 1 == (j - 1) // 2")
for _ in range(300):
    h = [random.randint(-50, 50) for _ in range(random.randint(1, 60))]
    heapq.heapify(h)
    for _ in range(random.randint(0, 20)):
        if random.random() < 0.5 and h:
            heapq.heappop(h)
        else:
            heapq.heappush(h, random.randint(-50, 50))
    n = len(h)
    for k in range(n):  # 0-based 규칙
        for c in (2 * k + 1, 2 * k + 2):
            if c < n:
                check(h[k] <= h[c], "heapq 0-based 불변식")
    for i in range(2, n + 1):  # 같은 리스트를 1-based로 읽기
        check(h[i // 2 - 1] <= h[i - 1], "1-based로 읽어도 부모 i // 2")
# j 자체의 2진 표현으로는 자리 붙이기가 아니다
check(bits(1) == "1" and bits(3) == "11" and bits(4) == "100", "heapq 칸 1의 자식 3 = 11₂, 4 = 100₂")
check(bits(3) == bits(1) + "1", "3은 1 끝에 1을 붙인 수")
check(bits(4) not in (bits(1) + "0", bits(1) + "1") and bits(4)[:-1] != bits(1), "4는 1에 자리 하나를 붙인 수가 아니다")

# ------------------------------------------------ 대응표 각 행 (전수)
for i in range(1, 20001):
    s = bits(i)
    for d in (0, 1):
        check(bits(2 * i + d) == s + str(d), f"자식 = 끝에 {d} 붙이기 ({i})")
        check(2 * i + d == (i << 1) + d == int(s + str(d), 2), "호너 한 걸음 = 2i + d")
    if i > 1:
        check(bits(i // 2) == s[:-1] and i // 2 == i >> 1, f"부모 = 끝자리 떼기 ({i})")
    end, _ = walk(s[1:])
    check(end == i, f"맨 앞 1 뒤의 자리 = 뿌리에서 오는 길 ({i})")
    check(depth_walk(i) == i.bit_length() - 1 == len(s) - 1 == floor_lg(i), f"깊이 = 자릿수 − 1 ({i})")
    # 호너 방법(밑 2)으로 문자열을 수로 바꾸기
    v = 0
    for ch in s:
        v = v * 2 + int(ch)
    check(v == i, "호너 방법")
    # 바꾸기 루프: i //= 2로 뗀 자리를 거꾸로 읽으면 길
    x, removed = i, []
    while x > 1:
        removed.append(x & 1)
        x //= 2
    check("".join(map(str, reversed(removed))) == s[1:], f"뗀 자리를 거꾸로 = 길 ({i})")

# 힙 층수 = 수 n의 2진 자릿수 (칸 n개, 마지막 번호 n)
for n in range(1, 5001):
    levels = max(depth_walk(i) for i in range(max(1, n // 2), n + 1)) + 1  # 가장 깊은 칸은 뒤쪽
    check(levels == n.bit_length() == floor_lg(n) + 1, f"힙 층수 ({n})")

# 세그먼트 트리: size, 잎 깊이, 잎 번호, 마디 수
for n in range(1, 3001):
    size = 1 << (n - 1).bit_length()
    check(size >= n and (size == 1 or size // 2 < n) and size & (size - 1) == 0, f"size = n 이상인 가장 작은 2의 거듭제곱 ({n})")
    K = size.bit_length() - 1
    check(K == ceil_lg(n) == (n - 1).bit_length(), f"잎 깊이 lg size = ceil(lg n) ({n})")
    for i in range(n):
        leaf = size + i
        check(depth_walk(leaf) == K, "잎 깊이")
        check(bits(leaf) == "1" + (format(i, f"0{K}b") if K else ""), f"잎 번호 = 1 + i를 K자리로 ({n}, {i})")
        lo, hi = node_range(leaf, size)
        check((lo, hi) == (i, i + 1), "잎이 맡은 칸")
for K in range(0, 12):
    size = 1 << K
    nodes = list(range(1, 2 * size))
    check(len(nodes) == 2 * size - 1 == sum(1 << d for d in range(K + 1)), "마디 2·size − 1개 = 1 + 2 + ⋯ + size")
    check(nodes == [x for x in range(1, 1 << (K + 2)) if len(bits(x)) <= K + 1], "마디 번호 = K + 1자리 이하 2진수 전체")
    check(bits(2 * size - 1) == "1" * (K + 1), "가장 큰 마디 = 11…1₂")
    check(len(range(0, 1 << (K + 1))) == 2 * size, "0까지 세면 2·size개라 '1 이상'이 필요하다")
    # node_range가 재귀로 반씩 나눈 것과 같은지
    def rec(v, lo, hi, out):
        out[v] = (lo, hi)
        if hi - lo > 1:
            m = (lo + hi) // 2
            rec(2 * v, lo, m, out)
            rec(2 * v + 1, m, hi, out)
    got = {}
    rec(1, 0, size, got)
    check(all(node_range(v, size) == got[v] for v in nodes), "마디가 맡은 칸")

# ------------------------------------------------ 공통 조상 = 가장 긴 공통 앞부분
for a in range(1, 2001):
    for b in range(1, 2001):
        if (a * 7 + b) % 5:  # 쌍의 1/5만 골라 시간 절약
            continue
        x = lca_brute(a, b)
        check(bits(x) == lcp(bits(a), bits(b)), f"LCA = LCP ({a}, {b})")
        check(lca(a, b) == x, f"비트 연산 lca ({a}, {b})")
for _ in range(20000):
    a, b = random.randint(1, 10**9), random.randint(1, 10**9)
    x = lca_brute(a, b)
    check(bits(x) == lcp(bits(a), bits(b)) and lca(a, b) == x, "무작위 LCA")
# 세그먼트 트리에서 칸 l, r을 둘 다 덮는 가장 작은 마디 = lca(size + l, size + r)
for K in range(0, 7):
    size = 1 << K
    for l in range(size):
        for r in range(l, size):
            cover = [v for v in range(1, 2 * size) if node_range(v, size)[0] <= l and r < node_range(v, size)[1]]
            best = min(cover, key=lambda v: node_range(v, size)[1] - node_range(v, size)[0])
            check(best == lca(size + l, size + r), f"두 칸을 덮는 가장 작은 마디 ({size}, {l}, {r})")

# ------------------------------------------------ 어디까지 같은가
# (1) 아무 이진 트리에서도 길 대응은 맞고, 빈칸 없는 번호는 위층·왼쪽부터 채운 나무뿐
broken_levels = False
for _ in range(2000):
    N = random.randint(1, 40)
    nodes = {1}
    while len(nodes) < N:
        p = random.choice(sorted(nodes))
        c = 2 * p + random.randint(0, 1)
        nodes.add(c)
    for v in nodes:
        if v > 1:
            check(v // 2 in nodes, "부모가 나무 안에 있다")
        check(depth_walk(v) == v.bit_length() - 1, "아무 나무에서도 깊이 = 자릿수 − 1")
    vs = sorted(nodes)
    for _ in range(20):
        a, b = random.choice(vs), random.choice(vs)
        x = lca_brute(a, b)
        check(x in nodes and bits(x) == lcp(bits(a), bits(b)), "아무 나무에서도 LCA = LCP")
    contiguous = nodes == set(range(1, N + 1))
    levels = max(depth_walk(v) for v in nodes) + 1
    if contiguous:
        check(levels == N.bit_length(), "빈칸 없는 번호면 층수 공식이 맞다")
    elif levels != N.bit_length():
        broken_levels = True
check(broken_levels, "빈칸 있는 나무에서는 층수 공식이 깨지는 경우가 있다")
# 오른쪽으로만 늘어진 나무: 1, 2, …, 30을 차례로 넣은 이진 탐색 트리
def bst_numbers(values):
    num = {}
    root = None
    child = {}
    for x in values:
        if root is None:
            root = x
            num[x] = 1
            continue
        cur = root
        while True:
            side = 0 if x < cur else 1
            nxt = child.get((cur, side))
            if nxt is None:
                child[(cur, side)] = x
                num[x] = 2 * num[cur] + side
                break
            cur = nxt
    return num
nums = bst_numbers(list(range(1, 31)))
check(sorted(nums.values()) == [(1 << k) - 1 for k in range(1, 31)], "번호 1, 3, 7, …, 2³⁰ − 1")
check(max(nums.values()) == 2**30 - 1 == 1073741823 and 2**30 - 1 > 10**9, "마지막 번호 2³⁰ − 1, 10억 넘음")
check(len(nums) == 30 and max(depth_walk(v) for v in nums.values()) + 1 == 30 != (30).bit_length(), "층수 30 ≠ 30의 자릿수 5")

# (2) 두 n: 힙 맨 아래 깊이 floor(lg n), 세그먼트 트리 잎 깊이 ceil(lg n)
for n in range(1, 5001):
    heap_bottom = max(depth_walk(i) for i in range(max(1, n // 2), n + 1))
    seg_leaf = ((1 << (n - 1).bit_length())).bit_length() - 1
    check(heap_bottom == floor_lg(n) and seg_leaf == ceil_lg(n), f"두 맨 아래 깊이 ({n})")
    pow2 = n & (n - 1) == 0
    check((heap_bottom == seg_leaf) == pow2, f"2의 거듭제곱일 때만 같다 ({n})")
    if not pow2:
        check(seg_leaf == heap_bottom + 1, "아니면 세그먼트 트리가 한 층 더 깊다")
check((floor_lg(5), ceil_lg(5)) == (2, 3) and (floor_lg(8), ceil_lg(8)) == (3, 3), "n = 5면 2와 3, n = 8이면 3과 3")

# (3) size를 늘리지 않은 아래에서 위로 판: 합은 맞고 잎 깊이는 다르다
def build(a, size):
    t = [0] * (2 * size)
    for i, v in enumerate(a):
        t[size + i] = v
    for i in range(size - 1, 0, -1):
        t[i] = t[2 * i] + t[2 * i + 1]
    return t


def update(t, size, i, v):
    i += size
    t[i] = v
    i //= 2
    while i >= 1:
        t[i] = t[2 * i] + t[2 * i + 1]
        i //= 2


def query(t, size, l, r, trace=None):
    res = 0
    l += size
    r += size
    while l < r:
        if trace is not None:
            trace.append((l & 1, r & 1))
        if l & 1:
            res += t[l]
            l += 1
        if r & 1:
            r -= 1
            res += t[r]
        l //= 2
        r //= 2
    return res


for n in range(1, 41):
    a = [random.randint(-9, 9) for _ in range(n)]
    t = build(a, n)  # size = n 그대로
    for _ in range(3):
        for l in range(n):
            for r in range(l + 1, n + 1):
                check(query(t, n, l, r) == sum(a[l:r]), f"size = n 판의 합 ({n}, {l}, {r})")
        i, v = random.randrange(n), random.randint(-9, 9)
        a[i] = v
        update(t, n, i, v)
check([bits(5 + i) for i in range(5)] == ["101", "110", "111", "1000", "1001"], "n = 5 잎 번호 101, 110, 111, 1000, 1001")
check([depth_walk(5 + i) for i in range(5)] == [2, 2, 2, 3, 3], "잎 깊이가 서로 다르다")
for n in range(1, 200):
    for v in range(1, 2 * n):
        end, _ = walk(bits(v)[1:])
        check(end == v, "size = n 판에서도 번호 = 1 + 길")
    if n & (n - 1):
        check(len({depth_walk(n + i) for i in range(n)}) == 2, f"2의 거듭제곱이 아니면 길 길이가 두 가지 ({n})")

# 재귀로 짜는 판(가운데에서 나눔): n = 5면 잎이 8, 9, 5, 6, 7번
def rec_leaves(n):
    leaf, mx = {}, 0
    def go(v, lo, hi, d=0, path=""):
        nonlocal mx
        mx = max(mx, v)
        check(d == v.bit_length() - 1 and bits(v) == "1" + path, "재귀 판에서도 깊이 = 자릿수 − 1, 번호 = 1 + 길")
        if lo == hi:
            leaf[lo] = v
            return
        mid = (lo + hi) // 2
        go(2 * v, lo, mid, d + 1, path + "0")
        go(2 * v + 1, mid + 1, hi, d + 1, path + "1")
    go(1, 0, n - 1)
    return leaf, mx
leaf5, _ = rec_leaves(5)
check([leaf5[i] for i in range(5)] == [8, 9, 5, 6, 7], "재귀 판 n = 5의 잎 8, 9, 5, 6, 7")
check([depth_walk(leaf5[i]) for i in range(5)] == [3, 3, 2, 2, 2], "재귀 판 잎 깊이도 다르다")
for n in range(1, 3001):
    leaf, mx = rec_leaves(n)
    check(mx < 4 * n, f"재귀 판 배열 4n칸이면 넉넉 ({n})")
    # 부모 = i // 2는 그대로(번호를 2v, 2v + 1로 매겼으므로), 깊이 = 자릿수 − 1도 그대로
    pow2 = n & (n - 1) == 0
    if not pow2:
        check(len({depth_walk(v) for v in leaf.values()}) > 1, f"2의 거듭제곱이 아니면 잎 깊이가 섞인다 ({n})")
        size = 1 << (n - 1).bit_length()
        check(any(leaf[i] != size + i for i in range(n)), "잎이 size + i가 아니다")
    else:
        size = n
        check(all(leaf[i] == size + i for i in range(n)), "2의 거듭제곱이면 두 판이 같다")

# (4) 묻기 코드: r은 원래 자리를 읽고, l은 받아올림 때문에 아니다
tr = []
query(build([0] * 8, 8), 8, 1, 4, tr)
check([x for x, _ in tr] == [1, 1], "size 8, [1, 4): l & 1이 1, 1")
check(bits(9) == "1001" and [9 & 1, (9 >> 1) & 1] == [1, 0], "9의 끝자리는 1, 0")
check([y for _, y in tr] == [12 & 1, (12 >> 1) & 1] == [0, 0], "r = 12는 원래 자리 0, 0을 읽는다")
mism_l = 0
for K in range(0, 7):
    size = 1 << K
    t = build([0] * size, size)
    for l in range(size):
        for r in range(l + 1, size + 1):
            tr = []
            query(t, size, l, r, tr)
            L, R = l + size, r + size
            check([y for _, y in tr] == [(R >> k) & 1 for k in range(len(tr))], "r 쪽은 원래 자리를 끝에서부터 읽는다")
            # l 쪽은 반씩 올림
            x, seq = L, []
            for _ in range(len(tr)):
                seq.append(x & 1)
                x = (x + 1) // 2
            check([p for p, _ in tr] == seq, "l 쪽은 반씩 올림(ceil(l / 2))")
            if [p for p, _ in tr] != [(L >> k) & 1 for k in range(len(tr))]:
                mism_l += 1
check(mism_l > 0, "l 쪽은 원래 자리와 다른 경우가 있다")

# (5) 중위 순서 번호: 끝에 붙은 0의 개수 = 높이(잎 0)
def inorder_positions(k):
    """칸 2^k − 1개 포화 이진 트리. 층 순서 번호 → 중위 순서 번호(1부터)."""
    pos, cnt = {}, 0
    def go(v):
        nonlocal cnt
        if v >= (1 << k):
            return
        go(2 * v)
        cnt += 1
        pos[v] = cnt
        go(2 * v + 1)
    go(1)
    return pos
def tz(p):
    return (p & -p).bit_length() - 1
for k in range(1, 12):
    pos = inorder_positions(k)
    for v, p in pos.items():
        height = (k - 1) - depth_walk(v)
        check(tz(p) == height, f"중위 번호의 끝 0 개수 = 높이 ({k}, {v})")
    check(pos[1] == 1 << (k - 1), "뿌리는 가운데 2^(k−1)")
p7 = inorder_positions(3)
check(p7[1] == 4 and bits(4) == "100", "칸 7개면 뿌리 4 = 100₂")
check(sorted(p7[v] for v in range(4, 8)) == [1, 3, 5, 7], "잎은 홀수 번호")
check(any(bits(p7[v])[1:] != bits(v)[1:] for v in p7), "중위 번호에는 길 대응이 없다")

# ------------------------------------------------ size 코드 두 가지 (C3 포함)
for n in range(1, 100001):
    good = 1 << (n - 1).bit_length()
    other = 1 << n.bit_length()
    check(good >= n and (good == 1 or good // 2 < n), "good은 n 이상인 가장 작은 2의 거듭제곱")
    check((n - 1).bit_length() == ceil_lg(n) and n.bit_length() == floor_lg(n) + 1, "정리 2·정리 1")
    pow2 = n & (n - 1) == 0
    check((other == good) == (not pow2), f"n이 2의 거듭제곱일 때만 다르다 ({n})")
    if pow2:
        check(other == 2 * good, "그때는 두 배")
check((1 << 5 .bit_length(), 1 << (5 - 1).bit_length()) == (8, 8), "n = 5: 8, 8")
check((1 << 6 .bit_length(), 1 << (6 - 1).bit_length()) == (8, 8), "n = 6: 8, 8")
check((1 << 8 .bit_length(), 1 << (8 - 1).bit_length()) == (16, 8), "n = 8: 16, 8")
check((1 << 1 .bit_length(), 1 << (1 - 1).bit_length()) == (2, 1), "n = 1: 2, 1")
# 큰 size로도 답은 맞다
for _ in range(200):
    n = random.randint(1, 70)
    a = [random.randint(-9, 9) for _ in range(n)]
    big = 1 << n.bit_length()
    t = build(a + [0] * (big - n), big)
    for _ in range(30):
        l = random.randrange(n)
        r = random.randint(l + 1, n)
        check(query(t, big, l, r) == sum(a[l:r]), "큰 size로도 합이 맞다")

# ------------------------------------------------ 카드
# C1: size 16, 5번 칸
check(16 + 5 == 21 and bits(21) == "10101" and format(5, "04b") == "0101", "C1 잎 21 = 10101₂")
end, seen = walk("0101")
check(end == 21 and seen == [1, 2, 5, 10, 21], "C1 지나는 마디 1, 2, 5, 10, 21")
check([node_range(v, 16) for v in seen] == [(0, 16), (0, 8), (4, 8), (4, 6), (5, 6)], "C1 맡은 칸 0~15, 0~7, 4~7, 4~5, 5")
end_wrong, seen_wrong = walk("101")
check(end_wrong == 13 and depth_walk(13) == 3 and node_range(13, 16) == (10, 12), "C1 흔한 오답: 13번 마디(10 ~ 11번 칸)")
check(16 .bit_length() - 1 == 4, "lg 16 = 4걸음")
# C2: (2p + d) // 2 == p, (i − 1) // 2는 1-based에서 틀린다
for p in range(1, 10000):
    for d in (0, 1):
        check((2 * p + d) // 2 == p and (2 * p + d) % 2 == d, "C2 몫 p, 나머지 d")
check((2 - 1) // 2 == 0 and 2 // 2 == 1, "C2 오답 식이면 2번 칸의 부모가 0")

# ------------------------------------------------ 전이 문제: 서브넷
a_, b_ = 130, 200
check(format(a_, "08b") == "10000010" and format(b_, "08b") == "11001000", "130, 200의 8자리 2진수")
pre = lcp(format(a_, "08b"), format(b_, "08b"))
check(pre == "1", "공통 앞부분은 첫 자리 1")
k = 24 + len(pre)
check(k == 25, "k = 25")
net = ipaddress.ip_network("192.168.1.130/25", strict=False)
check(str(net) == "192.168.1.128/25", "묶음 192.168.1.128/25")
check(ipaddress.ip_address("192.168.1.200") in net, "200도 들어 있다")
check(int(net.network_address) & 255 == 128 and int(net.broadcast_address) & 255 == 255, "범위 128 ~ 255")
check(int("10000000", 2) == 128 and int("11111111", 2) == 255, "10000000₂ ~ 11111111₂")
for k2 in range(26, 33):
    n2 = ipaddress.ip_network(f"192.168.1.130/{k2}", strict=False)
    check(ipaddress.ip_address("192.168.1.200") not in n2, f"/{k2}에는 둘이 함께 안 든다")
check(lca(256 + 130, 256 + 200) == 3 and depth_walk(3) == 1 and bits(3) == "11", "lca(386, 456) = 3번, 깊이 1")
# 흔한 오답: 차로 생각하기. 127과 128은 차가 1이지만 /24
check(format(127, "08b") == "01111111" and format(128, "08b") == "10000000", "127, 128의 2진수")
check(lcp(format(127, "08b"), format(128, "08b")) == "", "127과 128은 첫 자리부터 다르다")
n3 = ipaddress.ip_network("192.168.1.127/24", strict=False)
check(ipaddress.ip_address("192.168.1.128") in n3, "/24에 둘 다 든다")
for k3 in range(25, 33):
    n4 = ipaddress.ip_network(f"192.168.1.127/{k3}", strict=False)
    check(ipaddress.ip_address("192.168.1.128") not in n4, f"/{k3}에는 127과 128이 함께 안 든다")
check(200 - 130 == 70 and (70).bit_length() == 7 and 32 - 7 == 25, "차 70은 7비트, 32 − 7 = 25")
check(128 - 127 == 1 and 32 - (1).bit_length() == 31, "127, 128을 같은 셈으로 하면 /31")
n31 = ipaddress.ip_network("192.168.1.127/31", strict=False)
check(ipaddress.ip_address("192.168.1.128") not in n31, "/31에는 128이 안 든다")
# 묶음은 2^(32 − k)의 배수에서 시작한다: /25면 128의 배수
check(int(net.network_address) % 128 == 0, "128의 배수에서 시작")

print("ALL CHECKS PASSED")
