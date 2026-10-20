"""10.스택: 괄호 검사를 스택으로 구현하고 느린 방법과 비교한다."""
import itertools


def balanced(s):
    st = []
    for ch in s:
        if ch == "(":
            st.append(ch)
        else:
            if not st:
                return False
            st.pop()
    return not st


def balanced_slow(s):
    """'()'를 더는 없앨 수 없을 때까지 지운다. 빈 문자열이 되면 짝이 맞다."""
    while "()" in s:
        s = s.replace("()", "")
    return s == ""


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    count = 0
    for n in range(0, 13):
        for t in itertools.product("()", repeat=n):
            s = "".join(t)
            check(balanced(s) == balanced_slow(s), s)
            count += 1
    check(count == 2 ** 13 - 1, "문자열 개수")
    # 예시 표
    st, states = [], []
    for ch in "(()())":
        if ch == "(":
            st.append(ch)
        else:
            st.pop()
        states.append("".join(st))
    check(states == ["(", "((", "(", "((", "(", ""], "예시 표")
    check(balanced("(()())") and not balanced("())"), "예시")
    # C1
    st, out = [], []
    st.append(1); st.append(2); out.append(st.pop()); st.append(3); st.append(4); out.append(st.pop())
    check(out == [2, 4] and st == [1, 3], "C1")
    try:
        [].pop()
        check(False, "빈 스택 pop은 IndexError")
    except IndexError:
        pass
    print(f"괄호 문자열 {count}개 비교")
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
