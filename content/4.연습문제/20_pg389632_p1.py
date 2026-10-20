"""문자열과 알파벳과 쿼리 (프로그래머스 389632) 풀이와 검증. 문자 번호는 문제처럼 1부터 센다."""
import random
import time
from bisect import bisect_left, bisect_right


def solution(s, query, snap=None):
    n = len(s)
    pos = [[] for _ in range(26)]              # 글자마다 그 글자인 문자 번호들 (커지는 순)
    letter = [0] * (n + 1)
    idx = [0] * (n + 1)                        # 문자 번호 → pos[글자] 안의 자리
    for i, ch in enumerate(s, 1):
        c = ord(ch) - 97
        letter[i] = c
        idx[i] = len(pos[c])
        pos[c].append(i)

    parent, owner = [], []                     # 꼬리표의 유니온 파인드, 뿌리 꼬리표 → 문자열 번호

    def new_tag(sid):
        parent.append(len(parent))
        owner.append(sid)
        return len(parent) - 1

    def find(v):
        root = v
        while parent[root] != root:
            root = parent[root]
        while parent[v] != root:
            parent[v], v = root, parent[v]
        return root

    cur = [{}]                                 # 문자열마다: 글자 → 그 문자열의 그 글자 꼬리표(뿌리)
    starts = [[] for _ in range(26)]           # 글자마다: 구간이 시작하는 자리들
    tags = [[] for _ in range(26)]             # 글자마다: 구간의 꼬리표
    for c in range(26):
        if pos[c]:
            t = new_tag(0)
            cur[0][c] = t
            starts[c], tags[c] = [0], [t]

    def string_of(i):
        c = letter[i]
        j = bisect_right(starts[c], idx[i]) - 1
        return owner[find(tags[c][j])]

    result = []
    for q in query:
        p = q.split()
        if p[0] == "1":
            result.append("YES" if string_of(int(p[1])) == string_of(int(p[2])) else "NO")
        elif p[0] == "2":
            src = cur[string_of(int(p[1]))]
            new = len(cur)
            cur.append({})
            for c in {ord(ch) - 97 for ch in p[2]}:
                t = src.pop(c, None)
                if t is not None:              # 그 글자 꼬리표를 통째로 새 문자열에 넘긴다
                    owner[t] = new
                    cur[new][c] = t
        elif p[0] == "3":
            x, y = int(p[1]), int(p[2])
            new = len(cur)
            cur.append({})
            for c in {ord(ch) - 97 for ch in p[3]}:
                lo = bisect_left(pos[c], x)
                hi = bisect_right(pos[c], y) - 1
                if lo > hi:
                    continue
                t = new_tag(new)
                cur[new][c] = t
                st, tg = starts[c], tags[c]
                j = bisect_right(st, lo) - 1   # lo가 든 구간
                if st[j] != lo:                # lo 앞에서 자른다
                    st.insert(j + 1, lo)
                    tg.insert(j + 1, tg[j])
                    j += 1
                if hi + 1 < len(pos[c]):       # hi 뒤에서 자른다
                    j2 = bisect_right(st, hi + 1) - 1
                    if st[j2] != hi + 1:
                        st.insert(j2 + 1, hi + 1)
                        tg.insert(j2 + 1, tg[j2])
                e = bisect_right(st, hi)
                del st[j + 1:e], tg[j + 1:e]   # lo ~ hi를 구간 하나로
                tg[j] = t
        elif p[0] == "4":
            sx, sy = string_of(int(p[1])), string_of(int(p[2]))
            if sx == sy:
                continue
            old, young = min(sx, sy), max(sx, sy)
            dst = cur[old]
            for c, t in cur[young].items():
                if c in dst:
                    parent[t] = dst[c]         # 같은 글자 꼬리표끼리 잇는다
                else:
                    owner[t] = old
                    dst[c] = t
            cur[young] = {}
        elif p[0] == "5":                      # 마지막에 한 번
            cnt = {}
            for c in range(26):
                st, tg, size = starts[c], tags[c], len(pos[c])
                for j in range(len(st)):
                    length = (st[j + 1] if j + 1 < len(st) else size) - st[j]
                    sid = owner[find(tg[j])]
                    row = cnt.setdefault(sid, [0] * 26)
                    row[c] += length
            for sid in sorted(cnt):
                row = cnt[sid]
                if any(row):
                    result.append(" ".join(f"{chr(97 + c)} {row[c]}" for c in range(26) if row[c]))
        if snap is not None:                   # 6단계 표 확인용: 글자마다 (첫 번호, 끝 번호, 문자열)
            snap.append({chr(97 + c): [(pos[c][starts[c][j]],
                                        pos[c][(starts[c][j + 1] if j + 1 < len(starts[c]) else len(pos[c])) - 1],
                                        owner[find(tags[c][j])]) for j in range(len(starts[c]))]
                         for c in range(26) if pos[c]})
    return result


def by_simulation(s, query):
    """문자마다 속한 문자열 번호를 들고 그대로 따라 한다(작은 입력만)."""
    n = len(s)
    home = [0] * (n + 1)
    made = 1
    out = []
    for q in query:
        p = q.split()
        if p[0] == "1":
            out.append("YES" if home[int(p[1])] == home[int(p[2])] else "NO")
        elif p[0] == "2":
            src, word = home[int(p[1])], set(p[2])
            for i in range(1, n + 1):
                if home[i] == src and s[i - 1] in word:
                    home[i] = made
            made += 1
        elif p[0] == "3":
            x, y, word = int(p[1]), int(p[2]), set(p[3])
            for i in range(x, y + 1):
                if s[i - 1] in word:
                    home[i] = made
            made += 1
        elif p[0] == "4":
            a, b = home[int(p[1])], home[int(p[2])]
            old, young = min(a, b), max(a, b)
            for i in range(1, n + 1):
                if home[i] == young:
                    home[i] = old
        else:
            for sid in sorted(set(home[1:])):
                cnt = [0] * 26
                for i in range(1, n + 1):
                    if home[i] == sid:
                        cnt[ord(s[i - 1]) - 97] += 1
                out.append(" ".join(f"{chr(97 + c)} {cnt[c]}" for c in range(26) if cnt[c]))
    return out


def random_queries(n, qn, rng, letters, kinds="1234"):
    out = []
    for _ in range(qn - 1):
        kind = rng.choice(kinds)
        word = "".join(rng.choice(letters) for _ in range(rng.randint(1, 4)))
        x, y = sorted((rng.randint(1, n), rng.randint(1, n)))
        if kind == "1":
            out.append(f"1 {rng.randint(1, n)} {rng.randint(1, n)}")
        elif kind == "2":
            out.append(f"2 {x} {word}")
        elif kind == "3":
            out.append(f"3 {x} {y} {word}")
        else:
            out.append(f"4 {rng.randint(1, n)} {rng.randint(1, n)}")
    return out + ["5"]


if __name__ == "__main__":
    assert solution("programmers", ["1 1 5", "2 1 rm", "1 1 5", "5"]) == \
        ["YES", "NO", "a 1 e 1 g 1 o 1 p 1 s 1", "m 2 r 3"]
    assert solution("abacadae", ["3 1 4 aa", "1 1 5", "4 1 7", "1 1 5", "5"]) == \
        ["NO", "YES", "a 4 b 1 c 1 d 1 e 1"]
    # 6단계 추적용 예
    q6 = ["3 2 6 ab", "1 1 3", "2 4 a", "1 3 5", "4 7 3", "1 3 7", "5"]
    assert solution("abababab", q6) == by_simulation("abababab", q6) == \
        ["NO", "YES", "YES", "a 4 b 1", "b 3"]
    sn = []
    solution("abababab", q6, sn)
    assert sn[0] == {"a": [(1, 1, 0), (3, 5, 1), (7, 7, 0)], "b": [(2, 6, 1), (8, 8, 0)]}
    assert sn[2] == {"a": [(1, 1, 0), (3, 5, 2), (7, 7, 0)], "b": [(2, 6, 1), (8, 8, 0)]}
    assert sn[4] == {"a": [(1, 1, 0), (3, 5, 0), (7, 7, 0)], "b": [(2, 6, 1), (8, 8, 0)]}
    rng = random.Random(389632)
    for _ in range(3000):
        n = rng.randint(1, 12)
        letters = "abc"[:rng.randint(1, 3)]
        s = "".join(rng.choice(letters) for _ in range(n))
        q = random_queries(n, rng.randint(1, 15), rng, letters)
        assert solution(s, q) == by_simulation(s, q), (s, q)
    # 글자 10만 개, 쿼리 20만 개: 무작위 쿼리, 그리고 26글자를 넓은 범위에서 옮기는 3번만
    n = 100_000
    s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(n))
    alpha = "abcdefghijklmnopqrstuvwxyz"
    mixed = []
    for _ in range(200_000 - 1):
        kind = rng.choice("1234")
        x, y = sorted((rng.randint(1, n), rng.randint(1, n)))
        word = "".join(rng.sample(alpha, rng.randint(1, 26)))
        mixed.append({"1": f"1 {x} {y}", "2": f"2 {x} {word}", "3": f"3 {x} {y} {word}", "4": f"4 {x} {y}"}[kind])
    mixed.append("5")
    worst = [f"3 {rng.randint(1, n // 2)} {rng.randint(n // 2, n)} {alpha}" for _ in range(200_000 - 1)] + ["5"]
    narrow = []
    for _ in range(200_000 - 1):
        x = rng.randint(1, n - 300)
        narrow.append(f"3 {x} {x + 300} {alpha}")       # 좁은 범위: 구간이 잘게 쪼개진다
    narrow.append("5")
    times = []
    for q in (mixed, worst, narrow):
        t0 = time.perf_counter()
        solution(s, q)
        times.append(time.perf_counter() - t0)
    assert max(times) < 30, times
    print(f"쿼리 20만 개: 섞인 것 {times[0]:.1f}s, 26글자 넓은 범위 {times[1]:.1f}s, 26글자 좁은 범위 {times[2]:.1f}s")
    print("ALL CHECKS PASSED")
