"""수학적 귀납법 ↔ 루프 불변식: 문서의 모든 수치와 주장을 계산으로 확인한다.

인덱스는 0-based(문서의 a[0..n-1]과 같다). 표준 라이브러리만 쓴다.
실험 통과는 증명이 아니다. 증명은 문서에 있고, 여기서는 작은 범위 전수와 무작위 입력으로 확인한다.
"""
import bisect
import itertools
import random

random.seed(38)


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ---------------------------------------------------------------- 불변식 정의
def left_ok(a, x, lo):
    """a[0..lo-1]은 모두 x 미만."""
    return all(v < x for v in a[:lo])


def right_ok(a, x, hi):
    """a[hi..n-1]은 모두 x 이상."""
    return all(v >= x for v in a[hi:])


def bounds_ok(a, lo, hi):
    return 0 <= lo <= hi <= len(a)


def inv(a, x, lo, hi):
    """문서의 불변식 I(lo, hi)."""
    return bounds_ok(a, lo, hi) and left_ok(a, x, lo) and right_ok(a, x, hi)


def weak_inv(a, x, lo, hi):
    """오른쪽 조건을 뺀 약한 불변식: 왼쪽 조건과 범위 조건."""
    return bounds_ok(a, lo, hi) and left_ok(a, x, lo)


def body(a, x, lo, hi, bad=False):
    """반복문 몸체 한 번. bad=True면 lo = mid + 1 대신 lo = mid."""
    mid = (lo + hi) // 2
    if a[mid] < x:  # mid가 범위를 넘으면 IndexError
        lo = mid if bad else mid + 1
    else:
        hi = mid
    return lo, hi


def lower_bound_traced(a, x):
    """바퀴 시작마다 불변식을 assert하며 lower_bound를 돈다. (답, 상태 목록)을 돌려준다."""
    lo, hi = 0, len(a)
    states = [(lo, hi)]
    while True:
        check(inv(a, x, lo, hi), f"바퀴 시작에서 불변식 깨짐: {a} {x} {(lo, hi)}")
        if not lo < hi:
            break
        before = hi - lo
        lo, hi = body(a, x, lo, hi)
        check(hi - lo <= before - 1, "hi - lo가 1 이상 줄지 않음")
        check(hi - lo >= 0, "hi - lo가 음수")
        states.append((lo, hi))
    return lo, states


def all_sorted_lists(max_len, max_val):
    for n in range(max_len + 1):
        for combo in itertools.combinations_with_replacement(range(max_val + 1), n):
            yield list(combo)


def ceil_log2(m):
    return (m - 1).bit_length() if m > 0 else 0


# ---------------------------------------------------------------- 1. 먼저 비교해 보기 표
# 홀수 합: k = 1 기저, 한 걸음 k^2 + (2k + 1) = (k + 1)^2, k = 4이면 16
check(1 == 1 ** 2, "기저 k = 1")
for k in range(0, 2001):
    check(k * k + (2 * k + 1) == (k + 1) ** 2, f"한 걸음 k = {k}")
    check(sum(2 * j - 1 for j in range(1, k + 1)) == k * k, f"홀수 합 k = {k}")
check(1 + 3 + 5 + 7 == 16, "k = 4 예")

# 12 활용의 반복문 s += 2k - 1: k번째 반복 뒤 s = k^2 (반복 변수 k가 곧 바퀴 수)
for n in range(0, 300):
    s = 0
    check(s == 0 * 0, "0바퀴 뒤")
    for k in range(1, n + 1):
        s += 2 * k - 1
        check(s == k * k, f"k = {k}번째 반복 뒤 s = k^2")
    check(s == n * n, "끝나면 s = n^2")

# lower_bound 예: a = [2, 4, 4, 7, 9, 12, 15, 20], x = 7
A = [2, 4, 4, 7, 9, 12, 15, 20]
ans, states = lower_bound_traced(A, 7)
check(states == [(0, 8), (0, 4), (3, 4), (3, 3)], f"예시 상태 {states}")
check(ans == 3 and A[3] == 7, "예시 답 3")
for lo, hi in states:
    check(inv(A, 7, lo, hi), "예시의 모든 상태에서 I")
# 초기화: 두 구간이 비어 있고 0 <= 0 <= n <= n
check(A[0:0] == [] and A[len(A):] == [], "초기화의 빈 구간")

# ---------------------------------------------------------------- 2. 바퀴마다 불변식, 끝남, 답 (전수 + 무작위)
MAXLEN, MAXVAL = 8, 5
lists = list(all_sorted_lists(MAXLEN, MAXVAL))
check(len(lists) == 3003, f"정렬 리스트 개수 {len(lists)}")
runs = 0
reached = set()  # 실제 실행이 닿은 (a, x, lo, hi)
for a in lists:
    for x in range(-1, MAXVAL + 2):
        ans, states = lower_bound_traced(a, x)
        reached.update((tuple(a), x, lo, hi) for lo, hi in states)
        check(ans == bisect.bisect_left(a, x), f"답 불일치 {a} {x}")
        check(len(states) - 1 <= ceil_log2(len(a) + 1), "바퀴 수")
        runs += 1
for _ in range(3000):
    n = random.randint(0, 60)
    a = sorted(random.randint(-30, 30) for _ in range(n))
    x = random.randint(-35, 35)
    ans, _ = lower_bound_traced(a, x)
    check(ans == bisect.bisect_left(a, x), "무작위 답 불일치")
    runs += 1

# ---------------------------------------------------------------- 3. 모든 상태 (lo, hi)에서 유지와 종료
maint_cases = 0
unreached_checked = 0  # 실제 실행이 닿지 않는데 I를 만족하는 상태
guardless_index_error = 0
weak_insufficient = 0
for a in lists:
    n = len(a)
    for x in range(-1, MAXVAL + 2):
        target = bisect.bisect_left(a, x)
        for lo in range(n + 1):
            for hi in range(lo, n + 1):
                I = inv(a, x, lo, hi)
                W = weak_inv(a, x, lo, hi)
                if lo < hi:
                    # 반복 조건이 있어야 lo <= mid < hi (C1: 유지도 반복 조건을 쓴다)
                    check(lo <= (lo + hi) // 2 < hi, "lo < hi이면 lo <= mid < hi")
                    nlo, nhi = body(a, x, lo, hi)
                    # 유지: I와 반복 조건이면 한 바퀴 뒤 I
                    if I:
                        check(inv(a, x, nlo, nhi), f"유지 실패 {a} {x} {(lo, hi)}")
                        maint_cases += 1
                        if (tuple(a), x, lo, hi) not in reached:
                            unreached_checked += 1
                    # 세 조건이 각각 따로 유지된다 (반복 조건이 있을 때)
                    if bounds_ok(a, lo, hi):
                        check(bounds_ok(a, nlo, nhi), "범위 조건 유지 실패")
                        if left_ok(a, x, lo):
                            check(left_ok(a, x, nlo), "왼쪽 조건 유지 실패")
                        if right_ok(a, x, hi):
                            check(right_ok(a, x, nhi), "오른쪽 조건 유지 실패")
                    if W:
                        check(weak_inv(a, x, nlo, nhi), "약한 불변식 유지 실패")
                    # lo = mid로 바꿔도 I는 지켜진다
                    if I:
                        blo, bhi = body(a, x, lo, hi, bad=True)
                        check(inv(a, x, blo, bhi), "lo = mid도 유지는 지킨다")
                    # 남은 칸 수: 한 바퀴 뒤 floor(m/2) 이하, m >= 3이면 m - 1 미만
                    m = hi - lo
                    check(nhi - nlo <= m // 2, "남은 칸 수 > floor(m/2)")
                else:
                    # 종료: I와 lo >= hi(= 반복 조건의 부정)면 lo == hi이고 lo가 답
                    if I:
                        check(lo == hi and lo == target, f"종료 실패 {a} {x} {lo}")
                    # 약한 불변식은 종료에 부족: lo == hi인데 답이 아닌 상태가 있다
                    if W and lo != target:
                        weak_insufficient += 1
                    # 반복 조건 없이 몸체를 돌리면: lo = hi = n에서 mid = n이라 a[n]
                    if I and lo == hi == n:
                        try:
                            body(a, x, lo, hi)
                        except IndexError:
                            guardless_index_error += 1
check(maint_cases > 100000, f"유지 확인 수 {maint_cases}")
# 모든 상태를 돌리면 실제 실행이 닿지 않는 상태까지 유지를 확인한다
check(unreached_checked > 0 and unreached_checked < maint_cases, f"닿지 않는 상태 {unreached_checked}")
check(weak_insufficient > 0, "약한 불변식이 종료에 부족한 상태가 없음")
check(guardless_index_error > 0, "반복 조건 없을 때 a[n]을 읽는 상태가 없음")
# 구체 예: a = [1, 5], x = 3, (lo, hi) = (0, 0)은 약한 불변식을 만족하지만 답은 1
check(weak_inv([1, 5], 3, 0, 0) and bisect.bisect_left([1, 5], 3) == 1, "약한 불변식 구체 예")
check(not inv([1, 5], 3, 0, 0), "구체 예는 I는 아니다")
# 반복 조건 없이 I만: lo = hi = n인 상태는 I를 만족하고 a[n]을 읽는다
try:
    check(inv([2, 4], 9, 2, 2), "lo = hi = n에서 I")
    body([2, 4], 9, 2, 2)
    check(False, "IndexError가 나야 한다")
except IndexError:
    pass

# ---------------------------------------------------------------- 4. 남은 칸 수와 강한 귀납
for m in range(1, 2001):
    for lo in (0, 1, 7, 1000):
        hi = lo + m
        mid = (lo + hi) // 2
        left_len, right_len = mid - lo, hi - (mid + 1)
        check(left_len == m // 2 and right_len == (m + 1) // 2 - 1, "남은 칸 수 공식")
        check(max(left_len, right_len) <= m // 2, "floor(m/2) 이하")
        if m >= 3:
            check(max(left_len, right_len) < m - 1, f"m = {m}에서 m - 1 미만")
        if m >= 2:
            check(min(left_len, right_len) < m - 1, "m >= 2이면 한쪽은 m - 1 미만")
# m = 8이면 4 또는 3
check((8 // 2, (8 + 1) // 2 - 1) == (4, 3), "m = 8 예")


def run_from(a, x, lo, hi, limit=10 ** 4):
    """상태 (lo, hi)에서 출발해 반복문을 끝까지 돈다. 멈추지 않으면 None."""
    for _ in range(limit):
        if not lo < hi:
            return lo
        lo, hi = body(a, x, lo, hi)
    return None


def lb_rec(a, x, lo, hi):
    """재귀로 쓴 이분 탐색."""
    if lo == hi:
        return lo
    mid = (lo + hi) // 2
    if a[mid] < x:
        return lb_rec(a, x, mid + 1, hi)
    return lb_rec(a, x, lo, mid)


# Q(m): I가 참이고 hi - lo = m인 아무 상태에서 출발해도 멈추고 답을 돌려준다
for a in lists:
    n = len(a)
    for x in range(-1, MAXVAL + 2):
        target = bisect.bisect_left(a, x)
        check(lb_rec(a, x, 0, n) == target, "재귀판 답")
        for lo in range(n + 1):
            for hi in range(lo, n + 1):
                if inv(a, x, lo, hi):
                    check(run_from(a, x, lo, hi) == target, "Q(m) 반복문")
                    check(lb_rec(a, x, lo, hi) == target, "Q(m) 재귀")

# ---------------------------------------------------------------- 5. lo = mid: 유지는 지키고 끝나지 않는다
def bad_states(a, x, limit=50):
    lo, hi = 0, len(a)
    seen = []
    for _ in range(limit):
        if not lo < hi:
            return seen, True
        check(inv(a, x, lo, hi), "lo = mid판 바퀴 시작에서 I")
        seen.append((lo, hi))
        lo, hi = body(a, x, lo, hi, bad=True)
    return seen, False


seen, halted = bad_states([2], 5)
check(not halted and set(seen) == {(0, 1)}, f"[2], 5에서 (0, 1)에 머문다: {seen[:3]}")
check(lower_bound_traced([2], 5)[0] == 1, "올바른 코드의 답은 1")
# hi = lo + 1이면 mid = lo
for lo in range(0, 100):
    check((lo + lo + 1) // 2 == lo, "hi = lo + 1이면 mid = lo")

# ---------------------------------------------------------------- 6. 매개변수 탐색 최소형: 같은 네 단계, 초기화는 ok(hi)에 기댄다
def min_true_traced(lo0, hi0, ok):
    lo, hi = lo0, hi0
    while True:
        check(ok(hi) and all(not ok(v) for v in range(lo0, lo)), "최소형 불변식")
        if not lo < hi:
            return lo
        before = hi - lo
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
        check(hi - lo <= before - 1, "최소형 끝남")


for _ in range(3000):
    lo0 = random.randint(-50, 50)
    hi0 = lo0 + random.randint(0, 80)
    k = random.randint(lo0, hi0)
    ok = (lambda k: (lambda v: v >= k))(k)
    check(min_true_traced(lo0, hi0, ok) == k, "최소형 답")


def min_true_plain(lo, hi, ok):
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


# ok(hi)가 거짓이면(참인 값이 없으면) 기저가 거짓이고, 틀은 답이 아닌 hi를 돌려준다
r = min_true_plain(0, 10, lambda v: False)
check(r == 10, "참이 없으면 hi를 돌려준다")
for _ in range(1000):
    lo0 = random.randint(-50, 50)
    hi0 = lo0 + random.randint(0, 80)
    k = hi0 + random.randint(1, 20)  # 참인 값이 범위 밖에만 있다
    ok = (lambda k: (lambda v: v >= k))(k)
    r = min_true_plain(lo0, hi0, ok)
    check(r == hi0 and not ok(r), "기저가 거짓이면 답이 아닌 hi")

# ---------------------------------------------------------------- 7. 전이 문제: 빠른 거듭제곱
def fast_pow_traced(a, E):
    r, b, e = 1, a, E
    rounds = 0
    while True:
        check(r * b ** e == a ** E, f"불변식 r*b^e = a^E 깨짐 {a} {E}")
        if not e > 0:
            break
        before = e
        if e & 1:
            r *= b
            # 바퀴 중간: r * b^e가 a^E * b가 된다
            check(r * b ** e == a ** E * b, "중간 값 a^E * b")
            if a >= 2:
                check(r * b ** e != a ** E, "a >= 2이면 중간에 깨진다")
        b *= b
        e >>= 1
        check(0 <= e < before and e == before // 2, "e가 floor(e/2)로 준다")
        rounds += 1
    check(e == 0 and r == a ** E, "종료: r = a^E")
    return r, rounds


for a in range(0, 21):
    for E in range(0, 130):
        r, rounds = fast_pow_traced(a, E)
        check(rounds == E.bit_length(), "바퀴 수 = E의 2진 자릿수")
check(0 ** 0 == 1 and fast_pow_traced(0, 0)[0] == 1, "E = 0이면 반복하지 않고 r = 1")
check(fast_pow_traced(3, 5)[0] == 243, "3^5")

print(f"lower_bound 실행 {runs}회, 유지 확인 {maint_cases}개 상태(실제 실행이 닿지 않는 상태 {unreached_checked}개 포함)")
print("ALL CHECKS PASSED")
