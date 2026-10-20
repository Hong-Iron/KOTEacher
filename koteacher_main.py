"""KOTEacher 진입점 (PyInstaller가 묶는 파일).

    KOTEacher              → 앱 창
    KOTEacher --harness    → 학생 코드 검사 (표준 입력으로 요청)
    KOTEacher --capture F  → 문제 팩 만들기
"""
import sys

def _std_streams():
    """윈도의 창 앱(콘솔 없음)은 sys.stdin/stdout이 None이다. 하위 작업으로 불렸을 때는
    부모가 넘긴 파이프(0, 1, 2번)를 직접 연다."""
    for name, fd, mode in (("stdin", 0, "r"), ("stdout", 1, "w"), ("stderr", 2, "w")):
        stream = getattr(sys, name)
        if stream is None:
            try:
                setattr(sys, name, open(fd, mode, encoding="utf-8", closefd=False))
            except OSError:
                pass
        elif hasattr(stream, "reconfigure"):  # 윈도 기본 인코딩(cp1252 등)이면 한글이 깨진다
            stream.reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--harness", "--capture", "--run"):
        _std_streams()
    if len(sys.argv) > 1 and sys.argv[1] == "--harness":
        sys.argv = sys.argv[:1]
        from koteacher import harness
        sys.setrecursionlimit(10 ** 6)
        harness.main()
    elif len(sys.argv) > 1 and sys.argv[1] == "--run":
        import runpy
        path = sys.argv[2]
        sys.argv = [path]
        runpy.run_path(path, run_name="__main__")
    elif len(sys.argv) > 1 and sys.argv[1] == "--capture":
        from koteacher import capture
        capture.main(sys.argv[2])
    else:
        from koteacher.app import main
        main()
