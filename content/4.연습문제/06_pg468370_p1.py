"""중요한 단어를 스포 방지 (프로그래머스 468370) 풀이와 검증."""
import random


def solution(message, spoiler_ranges):
    n = len(message)
    hidden = [False] * n
    for s, e in spoiler_ranges:
        for i in range(s, e + 1):
            hidden[i] = True
    words = []
    start = 0
    for i in range(n + 1):
        if i == n or message[i] == " ":
            if i > start:
                words.append((message[start:i], any(hidden[start:i])))
            start = i + 1
    normal = {w for w, h in words if not h}
    seen = set()
    count = 0
    for w, h in words:
        if h:
            if w not in normal and w not in seen:
                count += 1
            seen.add(w)
    return count


def literal(message, spoiler_ranges):
    """구간을 하나씩 연다. 연 뒤 모든 글자가 드러난 스포 단어를 왼쪽부터 판정한다."""
    spans, i = [], 0
    for w in message.split(" "):
        spans.append((w, i, i + len(w) - 1))
        i += len(w) + 1
    covered = set()
    for s, e in spoiler_ranges:
        covered.update(range(s, e + 1))
    spoiler = [(w, a, b) for w, a, b in spans if any(k in covered for k in range(a, b + 1))]
    normal_words = {w for w, a, b in spans if not any(k in covered for k in range(a, b + 1))}
    opened = set()
    revealed_words = []
    done = set()
    count = 0
    for s, e in spoiler_ranges:
        opened.update(range(s, e + 1))
        now = [(w, a, b) for w, a, b in spoiler
               if (a, b) not in done and all(k in opened or k not in covered for k in range(a, b + 1))]
        for w, a, b in sorted(now, key=lambda x: x[1]):
            done.add((a, b))
            if w not in normal_words and w not in revealed_words:
                count += 1
            revealed_words.append(w)
    return count


def rand_case(rng):
    vocab = ["a", "b", "ab", "ba", "c1", "zz", "q"]
    words = [rng.choice(vocab) for _ in range(rng.randint(1, 12))]
    msg = " ".join(words)
    n = len(msg)
    ranges, pos = [], 0
    while pos < n and len(ranges) < 6:
        s = rng.randint(pos, n - 1)
        e = rng.randint(s, min(n - 1, s + 4))
        ranges.append([s, e])
        pos = e + 1 + rng.randint(0, 3)
    if not ranges:
        ranges = [[0, 0]]
    return msg, ranges


if __name__ == "__main__":
    assert solution("here is muzi here is a secret message", [[0, 3], [23, 28]]) == 1
    assert solution("my phone number is 01012345678 and may i have your phone number",
                    [[5, 5], [25, 28], [34, 40], [53, 59]]) == 4
    assert solution("cat dog cat bird", [[4, 4], [12, 15]]) == 2
    rng = random.Random(468370)
    for _ in range(3000):
        msg, ranges = rand_case(rng)
        assert solution(msg, ranges) == literal(msg, ranges), (msg, ranges)
    print("ALL CHECKS PASSED")
