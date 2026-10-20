"""KOTEacher 진입점 (PyInstaller가 묶는 파일).

    KOTEacher              → 앱 창
    KOTEacher --harness    → 학생 코드 검사 (표준 입력으로 요청)
    KOTEacher --capture F  → 문제 팩 만들기
"""
import sys

if __name__ == "__main__":
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
