"""붕대 감기 (프로그래머스 250137) 풀이와 검증."""
import random


def solution(bandage, health, attacks):
    t, x, y = bandage
    hp, streak = health, 0
    attack_at = {when: dmg for when, dmg in attacks}
    last = attacks[-1][0]
    for time in range(1, last + 1):
        if time in attack_at:
            hp -= attack_at[time]
            streak = 0
            if hp <= 0:
                return -1
        else:
            streak += 1
            hp += x
            if streak == t:
                hp += y
                streak = 0
            hp = min(hp, health)
    return hp


def by_gaps(bandage, health, attacks):
    """공격 사이의 빈 시간 g초를 한 번에: g*x + (g // t)*y 회복."""
    t, x, y = bandage
    hp, prev = health, 0
    for when, dmg in attacks:
        g = when - prev - 1
        hp = min(health, hp + g * x + (g // t) * y)
        hp -= dmg
        if hp <= 0:
            return -1
        prev = when
    return hp


if __name__ == "__main__":
    assert solution([5, 1, 5], 30, [[2, 10], [9, 15], [10, 5], [11, 5]]) == 5
    assert solution([3, 2, 7], 20, [[1, 15], [5, 16], [8, 6]]) == -1
    assert solution([4, 2, 7], 20, [[1, 15], [5, 16], [8, 6]]) == -1
    assert solution([1, 1, 1], 5, [[1, 2], [3, 2]]) == 3
    assert solution([3, 1, 2], 10, [[2, 4], [7, 3]]) == 7
    rng = random.Random(250137)
    for _ in range(3000):
        bandage = [rng.randint(1, 6), rng.randint(1, 5), rng.randint(1, 5)]
        health = rng.randint(1, 40)
        times = sorted(rng.sample(range(1, 60), rng.randint(1, 8)))
        attacks = [[w, rng.randint(1, 15)] for w in times]
        assert solution(bandage, health, attacks) == by_gaps(bandage, health, attacks)
    print("ALL CHECKS PASSED")
