"""코치 파이프라인의 결정적 단계 시험: 반례 줄이기, 위치 좁히기(SBFL), 수리 검증, 알려진 실수 지문."""
import ast, math, random, sys, time, copy

VAULT = str(__import__("pathlib").Path(__file__).resolve().parent.parent / "content/4.연습문제/18_pg67258_p1.py")
src = open(VAULT).read()
mod = ast.parse(src)
defs = ast.Module([n for n in mod.body if not (isinstance(n, ast.If))], [])
ns = {}
exec(compile(defs, "ref", "exec"), ns)
ref = ns["solution"]

USER = '''def solution(gems):
    kinds = len(set(gems))
    count = {}
    left = 0
    best = [1, len(gems)]
    for right, g in enumerate(gems):
        count[g] = count.get(g, 0) + 1
        while count[gems[left]] > 1:
            count[gems[left]] -= 1
            left += 1
        if len(count) == kinds and right - left <= best[1] - best[0]:
            best = [left + 1, right + 1]
    return best
'''
EXAMPLES = [(["DIA", "RUBY", "RUBY", "DIA", "DIA", "EMERALD", "SAPPHIRE", "DIA"], [3, 7]),
            (["AA", "AB", "AC", "AA", "AC"], [1, 3]), (["XYZ", "XYZ", "XYZ"], [1, 1]),
            (["ZZZ", "YYY", "NNNN", "YYY", "BBB"], [1, 5])]

def gen(rng, size):
    k = rng.randint(1, 4)
    return [rng.choice("ABCD"[:k]) for _ in range(size)]

def load(code):
    g = {}
    exec(compile(code if isinstance(code, ast.AST) else code, "user", "exec"), g)
    return g["solution"]

def run_cov(fn, args):
    lines = set(); prev = [None]
    def tr(frame, ev, arg):
        if frame.f_code.co_filename == "user":
            if ev == "line":
                lines.add((prev[0], frame.f_lineno)); prev[0] = frame.f_lineno
            return tr
        return None
    sys.settrace(tr)
    try: out = fn(copy.deepcopy(args))
    except Exception as e: out = ("ERR", type(e).__name__)
    finally: sys.settrace(None)
    return out, lines

user = load(USER)
t0 = time.perf_counter()
# 1. 예시
ex = [(g, w, user(list(g))) for g, w in EXAMPLES]
print("예시:", sum(o == w for g, w, o in ex), "/", len(ex), "통과")
# 2. 숨은 검사 + 반례 줄이기 (작은 크기부터)
rng = random.Random(1)
cex = None; tried = 0
for size in range(1, 16):
    for _ in range(80):
        g = gen(rng, size); tried += 1
        if user(list(g)) != ref(list(g)): cex = g; break
    if cex: break
# 원소 빼기로 더 줄이기
changed = True
while changed and len(cex) > 1:
    changed = False
    for i in range(len(cex)):
        c = cex[:i] + cex[i+1:]
        if c and user(list(c)) != ref(list(c)): cex = c; changed = True; break
print(f"반례: {cex} 기대 {ref(list(cex))} 내 답 {user(list(cex))} (입력 {tried}개 시도)")
# 3. 위치 좁히기 (Ochiai)
rng = random.Random(2)
ef = {}; ep = {}; nf = 0
for _ in range(400):
    g = gen(rng, rng.randint(1, 10))
    out, lines = run_cov(user, g)
    bad = out != ref(list(g)); nf += bad
    for l in lines:
        d = ef if bad else ep
        d[l] = d.get(l, 0) + 1
score = {l: ef.get(l, 0) / math.sqrt(nf * (ef.get(l, 0) + ep.get(l, 0))) for l in set(ef) | set(ep) if ef.get(l, 0)}
arcs = sorted(score.items(), key=lambda x: -x[1])
print("의심 분기:", [(f"{a}→{b}", round(v, 2)) for (a, b), v in arcs[:4]])
rank, seen = [], set()
for (a, b), v in arcs:
    if a and a not in seen: seen.add(a); rank.append((a, v))
rank = rank[:3]
print("의심 줄(분기의 출발 줄):", [l for l, _ in rank])
# 4. 수리 검증: 의심 줄에서 작은 변이를 시도
SWAP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
def mutants(tree, line):
    for node in ast.walk(tree):
        if getattr(node, "lineno", None) != line: continue
        if isinstance(node, ast.Compare):
            for i, op in enumerate(node.ops):
                if type(op) in SWAP:
                    yield f"{line}번 줄 비교 {type(op).__name__}→{SWAP[type(op)].__name__}", (id(node), "op", i)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            for d in (1, -1):
                yield f"{line}번 줄 상수 {node.value}→{node.value + d}", (id(node), "const", d)
def apply(code, target):
    tree = ast.parse(code); nodes = {id(n): n for n in ast.walk(tree)}
    return tree, target
fixes = []
rng = random.Random(3); probe = [gen(rng, rng.randint(1, 10)) for _ in range(300)] + [g for g, _ in EXAMPLES]
t1 = time.perf_counter(); n_mut = 0
for line in range(1, USER.count("\n") + 1):
    base = ast.parse(USER)
    for label, (nid, kind, arg) in list(mutants(base, line)):
        tree = ast.parse(USER)
        # 같은 위치의 노드를 새 트리에서 다시 찾는다
        old = [n for n in ast.walk(base)]; new = [n for n in ast.walk(tree)]
        node = new[[id(n) for n in old].index(nid)]
        if kind == "op": node.ops[arg] = SWAP[type(node.ops[arg])]()
        else: node.value += arg
        fn = load(tree); n_mut += 1
        try:
            if all(fn(list(g)) == ref(list(g)) for g in probe): fixes.append(label)
        except Exception:
            pass
print(f"모든 검사를 통과시키는 한 글자 수정: {fixes} (변이 {n_mut}개, {time.perf_counter() - t1:.2f}초)")
# 5. 알려진 실수 지문: 기준 풀이에 '흔한 실수'를 심은 변이체와 출력이 같은가
known = {"길이가 같을 때도 답을 바꿈(<→<=)": ("right - left < best[1] - best[0]", "right - left <= best[1] - best[0]"),
         "왼쪽을 줄이는 조건을 >=1로 씀": ("count[gems[left]] > 1", "count[gems[left]] >= 1")}
rsrc = ast.unparse(defs)
rng = random.Random(4); fp_in = [gen(rng, rng.randint(1, 8)) for _ in range(200)]
mine = [user(list(g)) for g in fp_in]
for name, (a, b) in known.items():
    assert a in rsrc, name
    try:
        m = load(rsrc.replace(a, b))
        theirs = [m(list(g)) for g in fp_in]
    except Exception as e:
        theirs = None
    print(f"지문 '{name}':", "일치" if theirs == mine else "다름")
print(f"결정적 단계 전체 {time.perf_counter() - t0:.2f}초")
