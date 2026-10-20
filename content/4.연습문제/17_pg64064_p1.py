"""불량 사용자 (프로그래머스 64064) 풀이와 검증."""
import random
from itertools import permutations


def solution(user_id, banned_id):
    def match(user, ban):
        return len(user) == len(ban) and all(b == "*" or b == u for u, b in zip(user, ban))

    results = set()
    used = []

    def go(i):
        if i == len(banned_id):
            results.add(frozenset(used))
            return
        for u in user_id:
            if u not in used and match(u, banned_id[i]):
                used.append(u)
                go(i + 1)
                used.pop()

    go(0)
    return len(results)


def by_permutations(user_id, banned_id):
    ok = lambda u, b: len(u) == len(b) and all(y in ("*", x) for x, y in zip(u, b))
    return len({frozenset(p) for p in permutations(user_id, len(banned_id))
                if all(ok(u, b) for u, b in zip(p, banned_id))})


if __name__ == "__main__":
    users = ["frodo", "fradi", "crodo", "abc123", "frodoc"]
    assert solution(users, ["fr*d*", "abc1**"]) == 2
    assert solution(users, ["*rodo", "*rodo", "******"]) == 2
    assert solution(users, ["fr*d*", "*rodo", "******", "******"]) == 3
    assert solution(["frodo", "fradi", "crodo"], ["fr*d*", "*rodo"]) == 3
    rng = random.Random(64064)
    for _ in range(2000):
        pool = {"".join(rng.choice("ab") for _ in range(rng.randint(1, 3))) for _ in range(rng.randint(1, 8))}
        users = sorted(pool)
        k = rng.randint(1, len(users))
        bans = []
        for u in rng.sample(users, k):
            bans.append("".join(c if rng.random() < 0.5 else "*" for c in u))
        assert solution(users, bans) == by_permutations(users, bans), (users, bans)
    print("ALL CHECKS PASSED")
