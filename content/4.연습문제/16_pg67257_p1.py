"""수식 최대화 (프로그래머스 67257) 풀이와 검증."""
import random
import re
from itertools import permutations


def solution(expression):
    tokens = re.split(r"([+\-*])", expression)
    tokens = [int(t) if t.isdigit() else t for t in tokens]
    calc = {"+": lambda a, b: a + b, "-": lambda a, b: a - b, "*": lambda a, b: a * b}
    best = 0
    for order in permutations(set(tokens[1::2])):
        t = tokens[:]
        for op in order:
            out = [t[0]]
            for i in range(1, len(t), 2):
                if t[i] == op:
                    out[-1] = calc[op](out[-1], t[i + 1])
                else:
                    out += [t[i], t[i + 1]]
            t = out
        best = max(best, abs(t[0]))
    return best


def evaluate(tokens, order):
    """order[-1](가장 낮은 우선순위)로 나누고 부분을 재귀로 계산해 왼쪽부터 합친다."""
    if len(tokens) == 1:
        return tokens[0]
    for k in range(len(order) - 1, -1, -1):
        op = order[k]
        if op in tokens[1::2]:
            parts, cur = [], [tokens[0]]
            for i in range(1, len(tokens), 2):
                if tokens[i] == op:
                    parts.append(cur)
                    cur = [tokens[i + 1]]
                else:
                    cur += [tokens[i], tokens[i + 1]]
            parts.append(cur)
            vals = [evaluate(p, order[:k]) for p in parts]
            acc = vals[0]
            for v in vals[1:]:
                acc = acc + v if op == "+" else acc - v if op == "-" else acc * v
            return acc
    raise ValueError("연산자 없음")


def slow(expression):
    tokens = [int(t) if t.isdigit() else t for t in re.split(r"([+\-*])", expression)]
    return max(abs(evaluate(tokens, list(o))) for o in permutations("+-*"))


if __name__ == "__main__":
    assert solution("100-200*300-500+20") == 60420
    assert solution("50*6-3*2") == 300
    assert solution("2-3*4") == 10
    rng = random.Random(67257)
    for _ in range(3000):
        n = rng.randint(2, 8)
        expr = str(rng.randint(0, 999))
        for _ in range(n - 1):
            expr += rng.choice("+-*") + str(rng.randint(0, 999))
        assert solution(expr) == slow(expr), expr
    print("ALL CHECKS PASSED")
