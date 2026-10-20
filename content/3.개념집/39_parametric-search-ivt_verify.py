"""39.매개변수 탐색 ↔ 사잇값 정리: 문서의 표, 수치, 주장, 전이 문제, 카드 답을 확인한다.

정수 쪽 코드는 0-based 정수 범위 [lo, hi]를 쓴다(21.매개변수 탐색의 min_true, max_true와 같다).
실수 쪽 이분법은 ok(x) = "f(x) >= 0"으로 읽는다: f(중점) >= 0이면 오른쪽 끝을, 아니면 왼쪽 끝을 중점으로 옮긴다.
"""
import itertools
import math
import random


# ---------- 정수 쪽: 21.매개변수 탐색의 두 틀 ----------
def min_true(lo, hi, ok, log=None):
    """거짓…거짓 참…참, ok(hi)는 참일 때 참인 가장 작은 x (단조가 아니면 경계 하나)."""
    while lo < hi:
        mid = (lo + hi) // 2
        r = ok(mid)
        if log is not None:
            log.append((lo, hi, mid, r))
        if r:
            hi = mid
        else:
            lo = mid + 1
    return lo


def max_true(lo, hi, ok, log=None):
    """참…참 거짓…거짓, ok(lo)는 참일 때 참인 가장 큰 x (단조가 아니면 경계 하나)."""
    while lo < hi:
        mid = (lo + hi + 1) // 2
        r = ok(mid)
        if log is not None:
            log.append((lo, hi, mid, r))
        if r:
            lo = mid
        else:
            hi = mid - 1
    return lo


# ---------- 실수 쪽: 이분법 ----------
def bisection(f, a, b, steps, log=None):
    """불변식 f(a) < 0 <= f(b)를 지키며 steps번 반으로 줄인다."""
    for _ in range(steps):
        p = (a + b) / 2
        fp = f(p)
        if log is not None:
            log.append((a, b, p, fp))
        if fp >= 0:
            b = p
        else:
            a = p
    return a, b


def check_comparison_table():
    # 왼쪽: 21.매개변수 탐색 C3의 판정 줄
    vals = [False, True, False, False, True]
    log = []
    r = min_true(0, 4, lambda x: vals[x], log)
    assert [(m, v) for _, _, m, v in log] == [(2, False), (3, False)]
    assert [(lo, hi) for lo, hi, _, _ in log] == [(0, 4), (3, 4)]
    assert r == 4 and vals[3] is False and vals[4] is True
    assert min(x for x in range(5) if vals[x]) == 1  # 참인 가장 작은 x

    # 오른쪽: f(x) = (x - 0.5)(x - 1.5)(x - 3.3)
    f = lambda x: (x - 0.5) * (x - 1.5) * (x - 3.3)
    assert [f(x) >= 0 for x in range(5)] == vals  # 정수 칸의 대답이 왼쪽 줄과 같다
    assert f(0) < 0 < f(4)
    log = []
    a, b = bisection(f, 0.0, 4.0, 4, log)
    mids = [p for _, _, p, _ in log]
    signs = ["+" if fp >= 0 else "-" for _, _, _, fp in log]
    assert mids == [2.0, 3.0, 3.5, 3.25] and signs == ["-", "-", "+", "-"]
    assert [(lo, hi) for lo, hi, _, _ in log] == [(0, 4), (2, 4), (3, 4), (3, 3.5)]
    assert (a, b) == (3.25, 3.5)
    a, b = bisection(f, 0.0, 4.0, 60)
    assert abs(a - 3.3) < 1e-12 and abs(b - 3.3) < 1e-12  # 3.3으로 모인다
    roots = sorted([0.5, 1.5, 3.3])
    assert all(abs(f(c)) < 1e-12 for c in roots) and roots[0] == 0.5  # 가장 작은 근 0.5


def check_invariants_exhaustive():
    """길이 1 ~ 12의 모든 참·거짓 줄로 약한 불변식, 돌려준 값의 성질, 판정 횟수를 확인한다."""
    start_returns = 0
    nonmono_total = 0
    for n in range(1, 13):
        cap = math.ceil(math.log2(n)) if n > 1 else 0
        for bits in itertools.product([False, True], repeat=n):
            seq = list(bits)
            mono_min = all(not seq[i] or seq[i + 1] for i in range(n - 1))   # F…F T…T
            mono_max = all(seq[i] or not seq[i + 1] for i in range(n - 1))   # T…T F…F
            # 최소형: ok(hi)는 참이어야 한다
            if seq[-1]:
                log = []
                r = min_true(0, n - 1, lambda x: seq[x], log)
                assert len(log) <= cap
                # 매 바퀴 시작의 약한 불변식: ok(hi) 참, lo가 시작점이 아니면 ok(lo - 1) 거짓
                for lo, hi, _, _ in log:
                    assert seq[hi] and (lo == 0 or not seq[lo - 1])
                # 대응표 3행: 거짓인 mid는 다음 바퀴의 lo - 1(실수 쪽의 새 a)이 되고, 참인 mid는 새 hi(새 b)가 된다
                for (lo, hi, mid, v), nxt in zip(log, log[1:] + [(r, r, None, None)]):
                    if v:
                        assert nxt[1] == mid and nxt[0] == lo
                    else:
                        assert nxt[0] - 1 == mid and nxt[1] == hi
                # 돌려준 r: ok(r) 참, r이 범위 시작이거나 ok(r - 1) 거짓
                assert seq[r] and (r == 0 or not seq[r - 1])
                # 거짓→참 이웃 쌍(범위 바로 앞 칸은 거짓으로 친다)이 늘 있다: 이산 사잇값 정리
                ext = [False] + seq
                assert any(not ext[i] and ext[i + 1] for i in range(n))
                if mono_min:
                    assert r == min(x for x in range(n) if seq[x])
                else:
                    nonmono_total += 1
                    if r == 0:
                        start_returns += 1
            # 최대형: ok(lo)는 참이어야 한다
            if seq[0]:
                log = []
                r = max_true(0, n - 1, lambda x: seq[x], log)
                assert len(log) <= cap
                for lo, hi, _, _ in log:
                    assert seq[lo] and (hi == n - 1 or not seq[hi + 1])
                assert seq[r] and (r == n - 1 or not seq[r + 1])
                if mono_max:
                    assert r == max(x for x in range(n) if seq[x])
    assert nonmono_total > 0 and start_returns > 0
    # 예: [참, 참, 거짓, 참] → 0
    ex = [True, True, False, True]
    assert min_true(0, 3, lambda x: ex[x]) == 0

    # 강한 불변식 "lo보다 작은 x는 모두 거짓"은 C3 줄에서 lo = 3일 때 깨진다(x = 1이 참)
    vals = [False, True, False, False, True]
    log = []
    min_true(0, 4, lambda x: vals[x], log)
    los = [lo for lo, _, _, _ in log] + [4]
    assert 3 in los and vals[1] is True
    # 그래도 약한 불변식은 남는다: lo = 3, hi = 4에서 ok(2) 거짓, ok(4) 참
    assert vals[2] is False and vals[4] is True


def check_local_check_is_blind():
    """끝난 뒤 'ok(r) 참, ok(r - 1) 거짓(범위 앞은 거짓)'을 확인해도 단조가 아닌 줄을 잡아내지 못한다."""
    rng = random.Random(39)
    caught = 0
    tested = 0
    while tested < 20000:
        n = rng.randint(3, 40)
        seq = [rng.random() < 0.5 for _ in range(n)]
        seq[-1] = True
        if all(not seq[i] or seq[i + 1] for i in range(n - 1)):
            continue  # 단조인 줄은 건너뛴다: 단조가 아닌 줄만 2만 개
        tested += 1
        r = min_true(0, n - 1, lambda x: seq[x])
        passes = seq[r] and (r == 0 or not seq[r - 1])
        if not passes:
            caught += 1
    assert tested == 20000 and caught == 0


def check_step_function():
    """통나무 예의 토막 수 ⌊8/L⌋ + ⌊5/L⌋ + ⌊11/L⌋는 실수 L에 대해 계단 함수다."""
    logs = [8, 5, 11]
    g = lambda L: sum(math.floor(x / L) for x in logs)
    rng = random.Random(1)
    flat = 0
    trials = 10000
    h = 1e-7
    for _ in range(trials):
        L = rng.uniform(1, 11)
        if g(L + h) == g(L):
            flat += 1
    assert flat / trials > 0.999  # 조금 바꾸면 대개 그대로: 기울기 0
    # 끊는 점에서는 뛴다(기울기가 없다): L = 4에서 ⌊8/L⌋이 2에서 1로 바뀐다
    assert g(4 - 1e-9) == 2 + 1 + 2 == 5 and g(4) == 5 and g(4 + 1e-9) == 1 + 1 + 2 == 4
    # 값은 늘 정수다
    assert all(isinstance(g(rng.uniform(1, 11)), int) for _ in range(100))


def check_nondecreasing_example():
    """f(x) = min(0, x) + max(0, x - 1): f(-1) = -1, f(2) = 1, [0, 1] 전체가 근. 이분법은 가장 왼쪽 0으로 간다."""
    f = lambda x: min(0.0, x) + max(0.0, x - 1)
    assert f(-1) == -1 and f(2) == 1
    assert all(f(k / 1000) == 0 for k in range(0, 1001))
    xs = [-1 + 3 * k / 1000 for k in range(1001)]
    assert all(f(x) <= f(y) for x, y in zip(xs, xs[1:]))  # 줄지 않는다
    log = []
    a, b = bisection(f, -1.0, 2.0, 60, log)
    assert abs(a) < 1e-15 and abs(b) < 1e-15
    # 줄지 않는 f에서는 강한 불변식(왼쪽 끝 왼쪽은 모두 음수)도 지켜진다
    for lo, hi, _, _ in log:
        assert all(f(x) < 0 for x in (lo - t * (lo + 1) for t in (0.0, 0.3, 0.7, 1.0)))
    # 무작위로 만든 줄지 않는 꺾은선(0인 평평한 구간 포함)에서도 가장 왼쪽 근으로 간다
    rng = random.Random(7)
    for _ in range(300):
        z0 = rng.uniform(-5, 5)
        z1 = z0 + rng.uniform(0, 3)
        s1, s2 = rng.uniform(0.1, 4), rng.uniform(0.1, 4)
        g = lambda x, z0=z0, z1=z1, s1=s1, s2=s2: s1 * min(0.0, x - z0) + s2 * max(0.0, x - z1)
        a0, b0 = z0 - rng.uniform(0.5, 4), z1 + rng.uniform(0.5, 4)
        a, b = bisection(g, a0, b0, 80)
        assert abs(b - z0) < 1e-9


def check_one_over_x():
    f = lambda x: 1 / x
    assert f(-1) < 0 < f(2)
    log = []
    a, b = bisection(f, -1.0, 2.0, 60, log)
    assert all(p != 0 for _, _, p, _ in log)  # 중점이 0에 닿지 않는다
    assert all(f(lo) < 0 <= f(hi) for lo, hi, _, _ in log)  # 끊겨 있어도 약한 불변식은 지켜진다
    assert abs(a) < 1e-15 and abs(b) < 1e-15  # 부호가 바뀌는 점 0으로 좁혀 간다
    assert all(f(x) != 0 for x in (-1 + 3 * k / 997 for k in range(998)) if x != 0)  # 근이 없다
    assert (-1.0 + 1.0) / 2 == 0.0  # [-1, 1]에서는 첫 중점이 0이라 1/x를 계산할 수 없다


def check_float_stall():
    u = math.ulp(1e9)
    assert u == 2.0 ** -23 and abs(u - 1.19e-7) < 0.01e-7
    lo = 1e9
    hi = math.nextafter(lo, math.inf)
    assert hi - lo == u
    mid = (lo + hi) / 2
    assert mid == lo or mid == hi  # 중점이 끝점과 같아진다
    # while hi - lo > 1e-9 는 끝나지 않는다 (답이 10^9 근처일 때)
    target = 1e9 + 0.3
    ok = lambda x: x >= target
    lo, hi = 0.0, 2e9
    it = 0
    while hi - lo > 1e-9 and it < 10000:
        m = (lo + hi) / 2
        if ok(m):
            hi = m
        else:
            lo = m
        it += 1
    assert it == 10000 and hi - lo == u  # 1만 번에서 끊었고 폭은 간격에 멈춰 있다


def check_hundred_iterations():
    w = 1e9 / 2 ** 100
    assert abs(w - 7.9e-22) < 0.05e-22
    rng = random.Random(100)
    targets = [1e9 - 0.3, 123456.789, 1.0, 1e-6, 3.7e-6, 0.0, 5e-13]
    targets += [rng.uniform(0, 1e9) for _ in range(200)]
    targets += [10 ** rng.uniform(-8, 9) for _ in range(200)]
    for c in targets:
        ok = lambda x: x >= c
        lo, hi = 0.0, 1e9
        if ok(lo):
            continue
        for _ in range(100):  # 정해진 횟수만큼 돈다: 반드시 끝난다
            m = (lo + hi) / 2
            if ok(m):
                hi = m
            else:
                lo = m
        assert lo < c <= hi  # 답을 끼운다
        # 남은 폭은 7.9e-22와 답 근처 부동소수점 간격 중 큰 쪽 정도다(중점 반올림 때문에 많아야 10% 차이)
        assert hi - lo <= 1.1 * max(w, math.ulp(c))
        if math.ulp(c) > 2 * w:  # 간격이 더 넓으면 이웃한 두 수에서 멈춘다
            assert math.nextafter(lo, math.inf) == hi
    # 답이 10^9 근처면 이웃한 두 수에서 멈추고, 그 폭은 약 1.19e-7이다
    c = 1e9 - 0.3
    lo, hi = 0.0, 1e9
    for _ in range(100):
        m = (lo + hi) / 2
        if m >= c:
            hi = m
        else:
            lo = m
    assert math.nextafter(lo, math.inf) == hi and abs((hi - lo) - 1.19e-7) < 0.01e-7


def check_proof_invariant():
    """증명의 불변식: f(a_k) < 0 <= f(b_k), b_k - a_k = (b - a)/2^k, a_k는 줄지 않고 b_k는 늘지 않는다."""
    funcs = [
        (lambda x: x ** 3 - x - 2, 1.0, 2.0),
        (lambda x: (x - 0.5) * (x - 1.5) * (x - 3.3), 0.0, 4.0),
        (lambda x: x - math.cos(x), 0.0, 1.0),
    ]
    for f, a, b in funcs:
        assert f(a) < 0 < f(b)
        A, B = a, b
        for k in range(1, 40):
            p = (A + B) / 2
            if f(p) >= 0:
                nA, nB = A, p
            else:
                nA, nB = p, B
            assert nA >= A and nB <= B
            A, B = nA, nB
            assert f(A) < 0 <= f(B)
            assert B - A == (b - a) / 2 ** k
        c = (A + B) / 2
        assert abs(f(c)) < 1e-9
    # 02 문서의 근 1.52138
    A, B = bisection(lambda x: x ** 3 - x - 2, 1.0, 2.0, 60)
    assert abs(A - 1.52138) < 5e-6


def check_transfer_problem():
    lo0, hi0 = 576, 9000
    m = hi0 - lo0 + 1
    assert m == 8425 and 2 ** 13 == 8192 < m <= 2 ** 14 and math.ceil(math.log2(m)) == 14
    worst = 0
    for mtu in range(lo0, hi0 + 1):
        log = []
        r = max_true(lo0, hi0, lambda x: x <= mtu, log)
        assert r == mtu and len(log) <= 14
        worst = max(worst, len(log))
    assert worst == 14  # 14번이 꼭 필요한 MTU가 있다
    # 4000 ~ 6000만 버리는 장비 (실제로는 9000까지 간다)
    ok = lambda x: x <= 9000 and not (4000 <= x <= 6000)
    log = []
    r = max_true(lo0, hi0, ok, log)
    assert log[0][2] == 4788 and log[0][3] is False
    assert r == 3999 and ok(r) and not ok(r + 1)
    assert max(x for x in range(lo0, hi0 + 1) if ok(x)) == 9000
    # 단조가 아니어도 돌려준 r은 늘 '간다 → 못 간다' 자리(또는 9000)
    rng = random.Random(576)
    for _ in range(300):
        cuts = sorted(rng.sample(range(lo0 + 1, hi0 + 1), rng.randint(1, 8)))
        bad = []
        for i in range(0, len(cuts) - 1, 2):
            bad.append((cuts[i], cuts[i + 1]))
        okr = lambda x, bad=bad: lo0 <= x <= hi0 and not any(s <= x <= e for s, e in bad)
        assert okr(lo0) and not okr(hi0 + 1)  # 576은 간다(문제의 전제), 9001은 못 간다
        r = max_true(lo0, hi0, okr)
        assert okr(r) and (r == hi0 or not okr(r + 1))


def find_cross(a):
    """a[0] < 0 <= a[-1]일 때 a[i] < 0 <= a[i + 1]인 i 하나. 본 칸 수도 돌려준다."""
    lo, hi = 0, len(a) - 1
    probes = 0
    while hi - lo > 1:
        mid = (lo + hi) // 2
        probes += 1
        if a[mid] < 0:
            lo = mid
        else:
            hi = mid
    return lo, probes


def check_card_c3():
    a = [-5, 3, -2, -7, 4, -1, 6]
    lo, hi = 0, len(a) - 1
    trace = []
    while hi - lo > 1:
        mid = (lo + hi) // 2
        trace.append((lo, hi, mid, a[mid]))
        if a[mid] < 0:
            lo = mid
        else:
            hi = mid
    assert trace == [(0, 6, 3, -7), (3, 6, 4, 4)]
    i, probes = find_cross(a)
    assert i == 3 and probes == 2 and a[3] < 0 <= a[4]
    assert a[0] < 0 <= a[1]  # 가장 앞의 i = 0은 놓친다
    rng = random.Random(3)
    for _ in range(20000):
        n = rng.randint(2, 60)
        arr = [rng.randint(-9, 9) for _ in range(n)]
        arr[0] = -rng.randint(1, 9)
        arr[-1] = rng.randint(0, 9)
        i, probes = find_cross(arr)
        assert arr[i] < 0 <= arr[i + 1]
        assert probes <= math.ceil(math.log2(n - 1)) if n > 2 else probes == 0


def check_card_c1():
    vals = [False, True, False, False, True]
    assert min_true(0, 4, lambda x: vals[x]) == 4 and not vals[3] and vals[4]


if __name__ == "__main__":
    check_comparison_table()
    check_invariants_exhaustive()
    check_local_check_is_blind()
    check_step_function()
    check_nondecreasing_example()
    check_one_over_x()
    check_float_stall()
    check_hundred_iterations()
    check_proof_invariant()
    check_transfer_problem()
    check_card_c1()
    check_card_c3()
    print("ALL CHECKS PASSED")
