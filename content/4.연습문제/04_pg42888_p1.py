"""오픈채팅방 (프로그래머스 42888) 풀이와 검증."""
import random


def solution(record):
    name = {}
    events = []
    for r in record:
        parts = r.split()
        action, uid = parts[0], parts[1]
        if action in ("Enter", "Change"):
            name[uid] = parts[2]
        if action == "Enter":
            events.append((uid, "들어왔습니다."))
        elif action == "Leave":
            events.append((uid, "나갔습니다."))
    return [f"{name[uid]}님이 {msg}" for uid, msg in events]


def slow(record):
    """이름이 바뀔 때마다 앞의 메시지를 모두 고쳐 쓴다."""
    msgs = []                 # [uid, 이름, 문구]
    for r in record:
        p = r.split()
        if p[0] in ("Enter", "Change"):
            for m in msgs:
                if m[0] == p[1]:
                    m[1] = p[2]
        if p[0] == "Enter":
            msgs.append([p[1], p[2], "들어왔습니다."])
        elif p[0] == "Leave":
            nm = next(m[1] for m in reversed(msgs) if m[0] == p[1])
            msgs.append([p[1], nm, "나갔습니다."])
    return [f"{nm}님이 {w}" for _, nm, w in msgs]


def rand_record(rng):
    users = [f"uid{i}" for i in range(rng.randint(1, 4))]
    inside = set()
    rec = []
    for _ in range(rng.randint(1, 25)):
        u = rng.choice(users)
        nick = rng.choice(["Muzi", "Prodo", "Ryan", "Con", "muzi"])
        if u in inside:
            if rng.random() < 0.5:
                rec.append(f"Leave {u}")
                inside.discard(u)
            else:
                rec.append(f"Change {u} {nick}")
        else:
            rec.append(f"Enter {u} {nick}")
            inside.add(u)
    return rec


if __name__ == "__main__":
    assert solution(["Enter uid1234 Muzi", "Enter uid4567 Prodo", "Leave uid1234", "Enter uid1234 Prodo",
                     "Change uid4567 Ryan"]) == ["Prodo님이 들어왔습니다.", "Ryan님이 들어왔습니다.",
                                                 "Prodo님이 나갔습니다.", "Prodo님이 들어왔습니다."]
    assert solution(["Enter u1 A", "Enter u2 B", "Change u1 C", "Leave u2"]) == \
        ["C님이 들어왔습니다.", "B님이 들어왔습니다.", "B님이 나갔습니다."]
    rng = random.Random(42888)
    for _ in range(2000):
        rec = rand_record(rng)
        assert solution(rec) == slow(rec), rec
    print("ALL CHECKS PASSED")
