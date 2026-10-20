"""캐시 (프로그래머스 17680) 풀이와 검증."""
import random
from collections import OrderedDict, deque


def solution(cacheSize, cities):
    cache = deque()
    time = 0
    for city in cities:
        city = city.lower()
        if city in cache:
            cache.remove(city)
            cache.append(city)
            time += 1
        else:
            time += 5
            if cacheSize == 0:
                continue
            if len(cache) == cacheSize:
                cache.popleft()
            cache.append(city)
    return time


def solution_maxlen(cacheSize, cities):
    cache = deque(maxlen=cacheSize)
    time = 0
    for city in map(str.lower, cities):
        if city in cache:
            cache.remove(city)
            time += 1
        else:
            time += 5
        cache.append(city)
    return time


def by_ordered(cacheSize, cities):
    cache, time = OrderedDict(), 0
    for c in cities:
        c = c.lower()
        if c in cache:
            cache.move_to_end(c)
            time += 1
        else:
            time += 5
            if cacheSize:
                if len(cache) == cacheSize:
                    cache.popitem(last=False)
                cache[c] = 1
    return time


if __name__ == "__main__":
    ex = [
        (3, ["Jeju", "Pangyo", "Seoul", "NewYork", "LA", "Jeju", "Pangyo", "Seoul", "NewYork", "LA"], 50),
        (3, ["Jeju", "Pangyo", "Seoul", "Jeju", "Pangyo", "Seoul", "Jeju", "Pangyo", "Seoul"], 21),
        (2, ["Jeju", "Pangyo", "Seoul", "NewYork", "LA", "SanFrancisco", "Seoul", "Rome", "Paris", "Jeju", "NewYork", "Rome"], 60),
        (5, ["Jeju", "Pangyo", "Seoul", "NewYork", "LA", "SanFrancisco", "Seoul", "Rome", "Paris", "Jeju", "NewYork", "Rome"], 52),
        (2, ["Jeju", "Pangyo", "NewYork", "newyork"], 16),
        (0, ["Jeju", "Pangyo", "Seoul", "NewYork", "LA"], 25),
        (2, ["a", "b", "a", "c", "b"], 21),
    ]
    for k, cities, want in ex:
        assert solution(k, cities) == want == solution_maxlen(k, cities) == by_ordered(k, cities), (k, cities)
    rng = random.Random(17680)
    for _ in range(3000):
        k = rng.randint(0, 5)
        cities = [rng.choice(["a", "A", "b", "B", "c", "d", "e", "f"]) for _ in range(rng.randint(1, 25))]
        assert solution(k, cities) == solution_maxlen(k, cities) == by_ordered(k, cities)
    print("ALL CHECKS PASSED")
