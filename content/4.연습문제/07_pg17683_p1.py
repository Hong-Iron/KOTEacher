"""방금그곡 (프로그래머스 17683) 풀이와 검증."""
import random


def solution(m, musicinfos):
    def norm(s):
        for a, b in (("C#", "c"), ("D#", "d"), ("F#", "f"),
                     ("G#", "g"), ("A#", "a"), ("B#", "b")):
            s = s.replace(a, b)
        return s

    def minutes(t):
        h, mm = map(int, t.split(":"))
        return h * 60 + mm

    m = norm(m)
    best, best_len = "(None)", 0
    for info in musicinfos:
        start, end, title, sheet = info.split(",")
        dur = minutes(end) - minutes(start)
        sheet = norm(sheet)
        played = (sheet * (dur // len(sheet) + 1))[:dur]
        if m in played and dur > best_len:
            best, best_len = title, dur
    return best


def tokens(s):
    out = []
    for ch in s:
        if ch == "#":
            out[-1] += "#"
        else:
            out.append(ch)
    return out


def other(m, musicinfos):
    mel = tokens(m)
    cands = []
    for idx, info in enumerate(musicinfos):
        a, b, title, sheet = info.split(",")
        dur = (int(b[:2]) * 60 + int(b[3:])) - (int(a[:2]) * 60 + int(a[3:]))
        notes = tokens(sheet)
        played = [notes[i % len(notes)] for i in range(dur)]
        L = len(mel)
        if any(played[i:i + L] == mel for i in range(len(played) - L + 1)):
            cands.append((-dur, idx, title))
    return min(cands)[2] if cands else "(None)"


NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def rand_case(rng):
    pool = rng.sample(NOTES, rng.randint(2, 4))
    infos = []
    for i in range(rng.randint(1, 5)):
        st = rng.randint(0, 1400)
        dur = rng.randint(1, 20)
        sheet = "".join(rng.choice(pool) for _ in range(rng.randint(1, 6)))
        infos.append(f"{st // 60:02d}:{st % 60:02d},{(st + dur) // 60:02d}:{(st + dur) % 60:02d},T{i},{sheet}")
    m = "".join(rng.choice(pool) for _ in range(rng.randint(1, 4)))
    return m, infos


if __name__ == "__main__":
    assert solution("ABCDEFG", ["12:00,12:14,HELLO,CDEFGAB", "13:00,13:05,WORLD,ABCDEF"]) == "HELLO"
    assert solution("CC#BCC#BCC#BCC#B", ["03:00,03:30,FOO,CC#B", "04:00,04:08,BAR,CC#BCC#BCC#B"]) == "FOO"
    assert solution("ABC", ["12:00,12:14,HELLO,C#DEFGAB", "13:00,13:05,WORLD,ABCDEF"]) == "WORLD"
    assert solution("CD", ["12:00,12:03,X,DC"]) == "X"
    assert solution("C", ["12:00,12:01,Y,C#"]) == "(None)"
    rng = random.Random(17683)
    for _ in range(3000):
        m, infos = rand_case(rng)
        assert solution(m, infos) == other(m, infos), (m, infos)
    print("ALL CHECKS PASSED")
