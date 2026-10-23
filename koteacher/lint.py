"""타이핑하는 동안의 정적 검사 (pyflakes). 코드를 실행하지 않고 읽기만 하므로 앱 프로세스에서 돌려도 안전하다.

실행해야 드러나는 NameError(예: import 없이 sqrt를 씀)를 그 줄에 닿기 전에 밑줄로 보여 준다.
"""
import ast

from pyflakes import checker, messages as M

# 오류(빨간 밑줄)로 볼 것: 실행하면 실패하는 것
ERRORS = (M.UndefinedName, M.UndefinedLocal, M.UndefinedExport, M.DuplicateArgument, M.ReturnOutsideFunction,
          M.YieldOutsideFunction, M.ContinueOutsideLoop, M.BreakOutsideLoop, M.TooManyExpressionsInStarredAssignment,
          M.TwoStarredExpressions)


def _korean(m):
    a = m.message_args
    if isinstance(m, M.UndefinedName):
        return f"'{a[0]}'이(가) 정의되지 않았습니다. 이 줄에 닿으면 NameError가 납니다. import나 변수 이름을 확인해 보세요"
    if isinstance(m, M.UndefinedLocal):
        return f"'{a[0]}'에 값을 넣기 전에 읽습니다 (UnboundLocalError)"
    if isinstance(m, M.UnusedImport):
        return f"{a[0]}을(를) 가져왔지만 쓰지 않습니다"
    if isinstance(m, M.UnusedVariable):
        return f"'{a[0]}'에 값을 넣었지만 쓰지 않습니다"
    if isinstance(m, M.RedefinedWhileUnused):
        return f"'{a[0]}'을(를) 쓰기 전에 다시 정의했습니다 ({a[1]}번 줄)"
    if isinstance(m, M.ImportShadowedByLoopVar):
        return f"반복 변수 '{a[0]}'이(가) 가져온 이름을 덮어씁니다 ({a[1]}번 줄)"
    if isinstance(m, M.DuplicateArgument):
        return f"매개변수 '{a[0]}'이(가) 두 번 나옵니다"
    if isinstance(m, M.ReturnOutsideFunction):
        return "함수 밖에서 return을 썼습니다"
    if isinstance(m, (M.ContinueOutsideLoop, M.BreakOutsideLoop)):
        return "반복문 밖에서 break/continue를 썼습니다"
    if isinstance(m, M.IsLiteral):
        return "is로 값(숫자·문자열)을 비교했습니다. 값 비교는 ==를 씁니다"
    if isinstance(m, M.FStringMissingPlaceholders):
        return "f-문자열인데 {}가 없습니다"
    if isinstance(m, M.IfTuple):
        return "if 조건이 튜플이라 항상 참입니다"
    return m.message % a


def lint(code):
    """[{line, col, end, severity: 'error'|'warning', msg}] (줄·칸은 1부터)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        line = e.lineno or 1
        return [{"line": line, "col": max(1, e.offset or 1), "end": (e.offset or 1) + 1, "severity": "error",
                 "msg": f"문법 오류: {e.msg}"}]
    out = []
    for m in checker.Checker(tree, filename="<내 코드>").messages:
        name = m.message_args[0] if m.message_args and isinstance(m.message_args[0], str) else ""
        col = m.col + 1
        out.append({"line": m.lineno, "col": col, "end": col + max(1, len(name)), "msg": _korean(m),
                    "severity": "error" if isinstance(m, ERRORS) else "warning"})
    return sorted(out, key=lambda x: (x["line"], x["col"]))
