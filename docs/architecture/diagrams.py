"""docs/architecture.md의 그림(SVG)을 만든다. 표준 라이브러리만 쓴다.

    python3 docs/architecture/diagrams.py

그림마다 상자·화살표·글자를 좌표로 적는다. 글자가 상자보다 길면 경고를 찍는다(한글 한 글자 ≈ 글자 크기, 영문·숫자 ≈ 0.58배).
어두운 화면에서도 읽히게 그림마다 흰 바탕을 깐다.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent
FONT = "'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif"
MONO = "Menlo,Consolas,'D2Coding',monospace"
INK, MUTED, LINE = "#1B2130", "#5B6476", "#8A92A3"
KIND = {  # 상자 종류: 바탕, 테두리
    "ui": ("#E8EEFC", "#2C56C9"),     # 화면(WebView)
    "py": ("#F1F3F7", "#8A92A3"),     # 파이썬 프로세스 안
    "proc": ("#FDF3E1", "#D99A1E"),   # 따로 도는 프로세스·서버
    "data": ("#E6F4EA", "#2E7D4A"),   # 파일·자료
    "warn": ("#FBE6E2", "#B93A27"),   # 막거나 버리는 길
    "plain": ("#FFFFFF", "#C5CBD6"),
}
WARN = []


def width(s, size, mono=False):
    if mono:
        return len(s) * size * 0.61
    return sum(size if ord(c) > 0x2E7F else size * 0.58 for c in s)


class Fig:
    def __init__(self, name, w, h, title, sub=""):
        self.name, self.w, self.h, self.parts, self.top = name, w, h, [], []  # top: 번호 동그라미 (상자 위에 그린다)
        self.text(24, 34, title, 18, "700")
        if sub:
            self.text(24, 56, sub, 12.5, color=MUTED)

    def text(self, x, y, s, size=13, weight="400", color=INK, anchor="start", mono=False, italic=False):
        fam = MONO if mono else FONT
        st = ' font-style="italic"' if italic else ""
        self.parts.append(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{weight}" '
                          f'fill="{color}" text-anchor="{anchor}"{st}>{escape(s)}</text>')

    def box(self, x, y, w, h, title=None, lines=(), kind="py", dashed=False, size=12.5, title_size=14, center=False, mono_lines=()):
        fill, stroke = KIND[kind]
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.4"{dash}/>')
        cy, cx = y + 22, (x + w / 2 if center else x + 12)
        anchor = "middle" if center else "start"
        if title:
            self._fit(title, title_size, w - 20, False)
            self.text(cx, cy, title, title_size, "700", anchor=anchor)
            cy += title_size + 6
        for ln in lines:
            mono = ln in mono_lines
            self._fit(ln, size, w - 20, mono)
            self.text(cx, cy, ln, size, color=INK if mono else MUTED, anchor=anchor, mono=mono)
            cy += size + 6
        if cy - (size + 6) + 8 > y + h:
            WARN.append(f"{self.name}: 상자 '{title or lines[0]}'의 높이가 모자랍니다 ({cy - y}px > {h}px)")

    def _fit(self, s, size, room, mono):
        if width(s, size, mono) > room:
            WARN.append(f"{self.name}: '{s}'가 상자보다 깁니다 ({width(s, size, mono):.0f}px > {room}px)")

    def arrow(self, pts, label=None, color=LINE, dashed=False, lx=None, ly=None, size=12, anchor="middle", label_color=None):
        """pts: [(x, y), …] 꺾은선. 끝에 화살촉."""
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        dash = ' stroke-dasharray="5 4"' if dashed else ""
        mid = "b" if color == "#2C56C9" else "c" if color == "#D99A1E" else "r" if color == "#B93A27" else "g" if color == "#2E7D4A" else "a"
        self.parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash} marker-end="url(#{mid})"/>')
        if label:
            if lx is None:
                (x1, y1), (x2, y2) = pts[0], pts[-1]
                lx, ly = (x1 + x2) / 2, (y1 + y2) / 2 - 6
            for i, part in enumerate(label.split("\n")):
                self.text(lx, ly + i * (size + 4), part, size, color=label_color or MUTED, anchor=anchor)

    def num(self, x, y, n, color="#2C56C9"):
        self.top.append(f'<circle cx="{x}" cy="{y}" r="10" fill="{color}"/>')
        self.text(x, y + 4.5, str(n), 11.5, "700", color="#FFFFFF", anchor="middle")
        self.top.append(self.parts.pop())

    def save(self):
        heads = "".join(
            f'<marker id="{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
            for k, c in (("a", LINE), ("b", "#2C56C9"), ("c", "#D99A1E"), ("r", "#B93A27"), ("g", "#2E7D4A")))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">'
               f"<defs>{heads}</defs>"
               f'<rect width="{self.w}" height="{self.h}" rx="14" fill="#FFFFFF"/>' + "".join(self.parts + self.top) + "</svg>\n")
        (OUT / f"{self.name}.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------- 1. 한 장 구조
def overview():
    f = Fig("01-overview", 980, 640, "KOTEacher 전체 구조", "서버 없이 로컬에서 동작한다: 앱 프로세스, 채점 서브프로세스, LLM 서버")
    f.box(24, 80, 300, 300, "창 (WebView)", [
        "맥 WKWebView · 윈도 WebView2가 그린다", "",
        "ui/index.html · app.js · style.css",
        "화면 6개: 홈 · 풀기 · 오답 노트 ·",
        "학습 · 풀이 기록 · 프로필", "",
        "Monaco 에디터", "KaTeX (수식) · Mermaid (다이어그램)"], kind="ui", mono_lines=("ui/index.html · app.js · style.css",))
    f.box(560, 80, 396, 300, "파이썬 프로세스 (koteacher/)", [], kind="plain")
    rows = [("api.py · Api", "JS가 호출하는 API, 시도별 Session 관리"),
            ("coach.py", "실패 정리 → 진단 → 응답 생성, 프로필, 유출 검사"),
            ("store.py", "SQLite: 시도·실행·코치 응답·오답·문서 질문"),
            ("vault.py · packs.py", "문제·개념 문서·힌트·팩 로드"),
            ("ollama.py · remote.py", "LLM 호출, 모델 다운로드, Ollama 실행")]
    for i, (a, b) in enumerate(rows):
        y = 118 + i * 51
        f.box(574, y, 368, 44, None, [], kind="py")
        f.text(586, y + 18, a, 12.5, "700", mono=True)
        f.text(586, y + 36, b, 11.5, color=MUTED)
    f.arrow([(324, 170), (560, 170)], "js_api 호출 (예: check(code))", color="#2C56C9", lx=442, ly=160)
    f.text(442, 192, "window.pywebview.api.이름(…)", 11.5, color=MUTED, anchor="middle", mono=True)
    f.arrow([(560, 270), (324, 270)], "이벤트 push (예: KG.on('say', …))", color="#2C56C9", lx=442, ly=260)
    f.text(442, 292, "window.evaluate_js(…)", 11.5, color=MUTED, anchor="middle", mono=True)
    f.text(442, 226, "pywebview 브리지", 13, "700", color="#2C56C9", anchor="middle")
    # 아래: 따로 도는 것과 파일
    f.box(24, 430, 220, 120, "채점 프로세스", ["koteacher/harness.py", "실행마다 새 서브프로세스", "테스트당 2초 제한"], kind="proc",
          mono_lines=("koteacher/harness.py",))
    f.box(262, 430, 220, 120, "Ollama 서버", ["127.0.0.1:11434", "로컬 LLM 추론 서버"], kind="proc", mono_lines=("127.0.0.1:11434",))
    f.box(500, 430, 200, 120, "외부 API (고를 때만)", ["OpenAI · Anthropic ·", "Gemini · OpenRouter ·", "Groq · OpenAI 호환"], kind="proc", dashed=True)
    f.box(718, 430, 238, 180, "파일", ["content/", "  문제 90 · 개념 문서 35", "packs/<문제>.json", "  예시·히든 테스트 입출력", "앱 데이터 폴더",
                                     "  koteacher.db · settings.json"], kind="data",
          mono_lines=("content/", "packs/<문제>.json"))
    f.arrow([(620, 380), (620, 405), (134, 405), (134, 430)], "코드와 팩 경로 → 결과 JSON", color="#D99A1E", lx=300, ly=399)
    f.arrow([(700, 380), (700, 415), (372, 415), (372, 430)], color="#D99A1E")
    f.arrow([(760, 380), (760, 420), (600, 420), (600, 430)], color="#D99A1E", dashed=True)
    f.arrow([(900, 380), (900, 430)], color="#2E7D4A")
    f.text(24, 600, "주황: 별도 프로세스·서버   초록: 파일   파랑: 프론트엔드   점선: 선택 사항", 12, color=MUTED)
    f.save()


# ---------------------------------------------------------------- 2. 실행 한 번
def check_flow():
    f = Fig("02-check-flow", 1000, 760, "실행 한 번의 흐름",
            "테스트 결과는 즉시 반환하고, 코치 응답은 백그라운드 스레드가 스트리밍한다")
    lanes = [("프론트엔드 (app.js)", "ui"), ("Api (api.py)", "py"), ("harness", "proc"), ("코치 (백그라운드)", "py"), ("Ollama", "proc")]
    xs = [30, 220, 410, 600, 800]
    for (name, kind), x in zip(lanes, xs):
        f.box(x, 74, 170, 36, name, [], kind=kind, center=True)
        f.parts.append(f'<line x1="{x + 85}" y1="110" x2="{x + 85}" y2="730" stroke="#D5DAE3" stroke-width="1.2" stroke-dasharray="4 4"/>')
    c = [x + 85 for x in xs]
    f.num(22, 153, 1)
    f.box(c[0] - 80, 128, 160, 50, None, ["실행 ⌘↵, 또는", "입력 멈춘 지 2.7초"], kind="ui", center=True, size=12)
    f.arrow([(c[0] + 80, 152), (c[1] - 4, 152)], "check(code)", color="#2C56C9", lx=(c[0] + 80 + c[1]) / 2, ly=146, size=11.5)
    f.num(c[1] - 18, 200, 2)
    f.arrow([(c[1], 200), (c[2] - 4, 200)], "코드 + 팩 경로 (stdin)", color="#D99A1E", lx=(c[1] + c[2]) / 2, ly=194, size=11.5)
    f.box(c[2] - 82, 212, 164, 214, "채점 순서", [
        "① 문법 검사", "② 예시 (테스트당 2초)", "③ 히든 테스트 ≤340개", "   (전체 3초,", "   첫 실패에서 중단)",
        "④ 최소 반례로", "   실행 추적", "⑤ 변이 탐색", "   (1.5초, 400개까지)"], kind="proc", size=11.5)
    f.num(c[2] + 95, 440, 3, "#D99A1E")
    f.arrow([(c[2], 426), (c[2], 450), (c[1] + 4, 450)], "결과 JSON (stdout)", color="#D99A1E", lx=(c[1] + c[2]) / 2, ly=444, size=11.5)
    f.box(c[1] - 82, 462, 164, 70, None, ["실패 정리 (facts)", "변이 탐색 성공 시", "확정 진단"], kind="py", size=11.5, center=True)
    f.num(c[1] - 22, 546, 4)
    f.arrow([(c[1] - 40, 532), (c[1] - 40, 556), (c[0] + 4, 556)], "테스트 결과 (즉시 반환)", color="#2C56C9", lx=(c[0] + c[1]) / 2 - 25, ly=550, size=11.5)
    f.box(c[0] - 80, 568, 160, 44, None, ["테스트 표 · 반례 표시"], kind="ui", center=True, size=12)
    f.num(c[1] + 95, 553, 5)
    f.arrow([(c[1] + 40, 532), (c[1] + 40, 568), (c[3] - 4, 568)], "백그라운드 스레드 (gen)", lx=(c[1] + c[3]) / 2 + 20, ly=562, size=11.5)
    f.box(c[3] - 82, 580, 164, 44, None, ["LLM 진단 (줄·말·분류)"], kind="py", center=True, size=11.5)
    f.arrow([(c[3] + 82, 596), (c[4] - 4, 596)], "/api/chat", color="#D99A1E", lx=(c[3] + 82 + c[4]) / 2, ly=590, size=11.5)
    f.arrow([(c[4] - 4, 612), (c[3] + 82, 612)], "토큰 스트림", color="#D99A1E", lx=(c[3] + 82 + c[4]) / 2, ly=628, size=11.5)
    f.num(c[3] + 95, 652, 6)
    f.box(c[3] - 82, 640, 164, 52, None, ["발화 정책 (Policy)", "speak · chip · none"], kind="py", center=True, size=11.5)
    f.arrow([(c[3] - 82, 666), (c[0] + 4, 666)], "line → stream → say / chip 이벤트", color="#2C56C9", lx=(c[0] + c[3]) / 2, ly=660, size=11.5)
    f.box(c[0] - 80, 678, 160, 50, None, ["말풍선: 그 줄 아래", "질문 하나"], kind="ui", center=True, size=12)
    f.save()


# ---------------------------------------------------------------- 3. 코치 파이프라인
def coach_pipeline():
    f = Fig("03-coach-pipeline", 1000, 545, "코치 파이프라인",
            "결정적인 방법부터 쓴다: 규칙 → 변이 탐색 → LLM. LLM 단계는 모델별 프로필을 쓴다")
    f.box(24, 90, 160, 120, "실패 정리", ["오류 > 오답 > 시간 초과", "같으면 입력이 짧은", "반례가 먼저"], kind="py", size=11.5)
    f.arrow([(184, 150), (214, 150)])
    f.box(214, 80, 250, 140, "진단 (diagnose)", [], kind="plain")
    tiers = [("규칙", "문법·불러오기 오류 → 그 줄", "확인됨"), ("변이 탐색", "한 곳 바꿔 모두 통과 → 그 줄", "확인됨"),
             ("LLM 진단", "실행 추적을 읽고 줄·말·분류", "추정")]
    for i, (a, b, conf) in enumerate(tiers):
        y = 108 + i * 36
        f.box(224, y, 230, 30, None, [], kind="proc" if a == "LLM 진단" else "py")
        f.text(234, y + 20, a, 12, "700")
        f.text(300, y + 20, b, 10.5, color=MUTED)
    f.arrow([(464, 150), (494, 150)])
    f.box(494, 80, 190, 140, "정책 (Policy)", ["문법 오류: 칩만", "조용히 모드: 칩만", "같은 말은 다시 안 함", "자동 검사: 180초에 한 번", "(normal 모드: 확정 진단만)"],
          kind="py", size=11.5)
    f.arrow([(684, 100), (720, 100)], "chip", lx=702, ly=92, size=11)
    f.arrow([(684, 180), (720, 180)], "speak", lx=702, ly=172, size=11)
    f.box(720, 80, 170, 40, None, ["접힌 칩 (누르면 말함)"], kind="plain", size=11.5, center=True)
    f.box(720, 140, 170, 70, "응답 생성 (say)", ["LLM이 질문 한 개"], kind="proc", size=11.5)
    f.arrow([(820, 210), (820, 248)])
    f.box(640, 248, 340, 150, "유출 검사 (leak_reason)", [
        "① 코드 모양 (def·for·대입문·```)", "② 모범 풀이 줄과 겹침", "③ 고칠 값을 '바꿔/써'와 함께 말함",
        "④ 'A 대신 B'(B가 코드), '~바꿔야 합니다'", "⑤ 320자 넘음"], kind="warn", size=11.5)
    f.arrow([(640, 340), (500, 340)], "통과", color="#2E7D4A", lx=570, ly=332, size=11.5, label_color="#2E7D4A")
    f.box(330, 312, 170, 56, None, ["말풍선에 질문 표시", "(coach_msgs에 저장)"], kind="ui", center=True, size=11.5)
    f.arrow([(810, 398), (810, 430)], "걸림", color="#B93A27", lx=838, ly=420, size=11.5, label_color="#B93A27")
    f.box(700, 430, 250, 68, None, ["확정 진단: 위반 사유를 붙여", "한 번 재생성", "LLM 진단: 바로 폴백"], kind="warn", center=True, size=11.5)
    f.arrow([(700, 464), (500, 464)], "폴백", color="#B93A27", lx=600, ly=456, size=11.5, label_color="#B93A27")
    f.box(330, 436, 170, 56, None, ["폴백 템플릿", "(줄과 반례만 언급)"], kind="ui", center=True, size=11.5)
    # 프로필
    f.box(24, 260, 280, 180, "프로필 선택 (profile)", [
        "모델 이름으로 고른다", "gemma → 기본", "mistral → Ministral용", "qwen·omnicoder → Qwen용",
        "시스템 프롬프트 · temperature", "메시지 구조 · 후처리"], kind="data", size=11.5)
    f.arrow([(164, 260), (164, 234), (760, 234), (760, 210)], color="#2E7D4A", dashed=True)
    f.arrow([(339, 234), (339, 220)], color="#2E7D4A", dashed=True)
    f.text(470, 252, "프로필 적용", 11, color="#2E7D4A", anchor="middle")
    f.text(24, 528, "주황: LLM 호출   빨강: 차단 경로   초록 점선: 프로필 적용", 12, color=MUTED)
    f.save()


# ---------------------------------------------------------------- 4. 자료와 기록
def data_flow():
    f = Fig("04-data", 1100, 620, "데이터 흐름: 팩 생성과 SQLite 기록")
    f.box(24, 80, 200, 110, "공부 볼트 (Obsidian)", ["알고리즘 개념 문서", "연습 문제 문서", "모범 풀이 코드 (*_p1.py)"], kind="data", size=11.5)
    f.arrow([(224, 135), (334, 135)], "sync_content.py", lx=279, ly=126, size=10.5)
    f.box(334, 80, 200, 110, "content/", ["4.연습문제: 문제 90", "  문서 + 모범 풀이 코드", "3.개념집: 개념 문서 35", "(수업 자료 언급·메모 제거)"], kind="data", size=11.5)
    f.arrow([(534, 135), (624, 135)], "capture.py", lx=579, ly=126, size=10.5)
    f.box(624, 80, 220, 110, "모범 풀이 __main__ 실행", ["solution 호출을 모두 기록", "random 쓰기 전 호출 → 예시", "그 뒤 호출 → 히든 테스트"], kind="proc", size=11.5)
    f.arrow([(844, 135), (884, 135)])
    f.box(884, 80, 192, 110, "팩 <문제>.json", ["인자 이름", "예시 입출력", "히든: 작은 입력 300", "+ 큰 입력 40"], kind="data", size=11.5)
    f.arrow([(980, 190), (980, 230)], "harness가 읽음", lx=980, ly=246, size=11)
    f.text(24, 290, "SQLite 테이블 (koteacher.db)과 쓰는 화면", 15, "700")
    tables = [("attempts", "row = 시도 1회", "시작·끝, 결과, 연 힌트 수, 풀이 봄"),
              ("snapshots", "row = 실행 1회", "그때 코드, 결과 요약, 통과 여부"),
              ("coach_msgs", "row = 코치 응답 1개", "진단 분류, 걸린 시간, 별점"),
              ("mistakes", "row = 고친 실수 1건", "고친 차이, 걸린 시간, 내 메모"),
              ("doc_notes", "row = 문서 질문 1개", "답, 이어서 물은 질문과 답")]
    screens = [("홈 문제 상태 · 추천 · 풀이 기록", (0, 1)), ("프로필 잔디 · 연속 일수", (1,)), ("다시 열 때 이어 쓸 코드", (1,)),
               ("풀이 기록의 코치 말", (2,)), ("오답 노트 · 약한 개념 추천", (3,)), ("문서 하이라이트 · 전체 검색", (4,))]
    for i, (t, a, b) in enumerate(tables):
        y = 310 + i * 58
        f.box(24, y, 420, 50, None, [], kind="py")
        f.text(36, y + 20, t, 12.5, "700", mono=True)
        f.text(140, y + 20, a, 12)
        f.text(140, y + 38, b, 11, color=MUTED)
    for j, (s, src) in enumerate(screens):
        y = 310 + j * 48
        f.box(740, y, 336, 38, None, [s], kind="ui", size=12)
        for k in src:
            f.arrow([(444, 335 + k * 58), (740, y + 19)], color="#9AA4B5")
    f.save()


# ---------------------------------------------------------------- 5. 통과 기록
def attempt_status():
    f = Fig("05-status", 980, 470, "문제 상태 판정", "문제 상태는 그 문제의 모든 시도 중 가장 좋은 결과다 (통과 > 힌트로 통과 > 시도)")
    f.box(24, 120, 130, 60, "새 문제", ["아직 실행 안 함"], kind="plain", size=11.5, center=True)
    f.arrow([(154, 150), (214, 150)], "실행", lx=184, ly=142, size=11.5)
    f.box(214, 120, 130, 60, "시도", ["검사를 못 넘김"], kind="warn", size=11.5, center=True)
    f.arrow([(344, 150), (404, 150)], "모두 통과", lx=374, ly=142, size=11.5)
    f.box(404, 90, 270, 130, "이 시도에서 받은 도움은?", ["힌트 2개 이상, 또는 풀이 봄", "→ 힌트로 통과", "실전 모드, 반례·코치·힌트 없이 제출", "→ 실전 통과", "그 밖 → 통과"],
          kind="py", size=11.5)
    for i, (name, kind) in enumerate((("힌트로 통과", "proc"), ("실전 통과", "ui"), ("통과", "data"))):
        f.arrow([(674, 130 + i * 40), (734, 130 + i * 40)])
        f.box(734, 112 + i * 40, 150, 34, None, [name], kind=kind, size=12, center=True)
    f.box(24, 270, 440, 160, "이어 쓰면 도움도 이어 받는다", [
        "문제를 다시 열 때 지난 코드를 불러오면, 그 코드를 쓴", "시도의 힌트 수와 '풀이 봄'을 새 시도에 함께 기록한다.",
        "'이 코드로 다시 열기', '이 코드 불러오기', '처음부터'도 같다.", "", "홈의 '다시 풀기'만 빈 기록으로 연다.",
        "(api.py: Session.carried_hints, _carry)"], kind="plain", size=11.5, mono_lines=("(api.py: Session.carried_hints, _carry)",))
    f.box(500, 270, 456, 160, "왜 이렇게 하나", [
        "힌트로 푼 코드를 다시 열면 자동 검사가 그 코드를 돌린다.", "도움을 이어 받지 않으면 힌트 0개인 새 시도가 통과해",
        "문제 상태가 '통과'로 바뀐다. 힌트를 이미 봤으므로", "'힌트로 통과'로 남는 쪽이 맞다.", "",
        "1개까지는 '통과'로 친다 (store.problem_status)."], kind="plain", size=11.5)
    f.save()


# ---------------------------------------------------------------- 6. 만들기와 첫 실행
def build_and_setup():
    f = Fig("06-build-setup", 1000, 556, "빌드·배포와 첫 실행")
    f.text(24, 90, "맥 (tools/build_mac.py)", 14, "700")
    steps = ["팩 90개 미리 빌드", "PyInstaller로 .app 번들", "ad-hoc 서명 (codesign -s -)", "번들 앱 자가 점검",
             "DMG (+ 설치하고 열기 스크립트)", "PKG (+ postinstall)"]
    for i, s in enumerate(steps):
        y = 104 + i * 52
        f.box(24, y, 220, 40, None, [s], kind="py", size=12, center=True)
        if i:
            f.arrow([(134, y - 12), (134, y)])
    f.text(270, 90, "윈도 (GitHub Actions)", 14, "700")
    wsteps = ["v* 태그 push", "build_win.py: PyInstaller", "Inno Setup → Setup.exe", "zip도 함께", "릴리스에 업로드"]
    for i, s in enumerate(wsteps):
        y = 104 + i * 52
        f.box(270, y, 220, 40, None, [s], kind="py", size=12, center=True)
        if i:
            f.arrow([(380, y - 12), (380, y)])
    f.box(24, 436, 466, 96, "한 줄 설치 (install.sh · install.ps1)", ["저장소를 받아 venv를 만들고 Ollama와 코치 모델까지 설치한다.", "인텔 맥과 리눅스용. curl로 받은 파일에는 quarantine 속성이",
                                                                  "붙지 않아 Gatekeeper 경고가 없다."], kind="plain", size=11.5)
    # 첫 실행
    f.text(540, 90, "첫 실행 (api.prepare_coach)", 14, "700")
    f.box(540, 104, 200, 40, None, ["앱 시작: 모델 있음?"], kind="ui", size=12, center=True)
    f.arrow([(740, 124), (790, 124)], "있음", lx=765, ly=116, size=11)
    f.box(790, 104, 186, 40, None, ["그대로 씀"], kind="data", size=12, center=True)
    f.arrow([(640, 144), (640, 180)], "없음", lx=665, ly=166, size=11)
    f.box(540, 180, 200, 40, None, ["Ollama가 켜져 있나?"], kind="py", size=12, center=True)
    f.arrow([(740, 200), (790, 200)], "꺼짐", lx=765, ly=192, size=11)
    f.box(790, 180, 186, 76, None, ["설치돼 있으면 켠다", "없으면: 맥은 버튼 하나로", "설치, 윈도는 안내"], kind="proc", size=11.5)
    f.arrow([(640, 220), (640, 270)], "켜짐", lx=665, ly=252, size=11)
    f.arrow([(883, 256), (883, 290), (740, 290)], color="#D99A1E")
    f.box(540, 270, 200, 60, None, ["팝업을 띄우고", "바로 e4b 받기 시작"], kind="ui", size=12, center=True)
    f.arrow([(640, 330), (640, 360)])
    f.box(540, 360, 436, 120, "모델 다운로드 (api.pull_model)", ["ghcr.io에서 받고, 끊기면 이어 받기로 3번까지 재시도", "그래도 실패하면 Ollama 레지스트리의 원본으로 폴백",
                                                             "진행률 · 속도 · 남은 시간 · 출처 표시", "팝업을 닫아도 계속 받고, 상단 바에 % 표시"], kind="plain", size=11.5)
    f.save()


# ---------------------------------------------------------------- 7. 파이프라인과 데이터
def pipeline():
    f = Fig("07-pipeline", 1000, 750, "채점·코치 파이프라인과 단계 사이의 데이터",
            "가운데가 실행 한 번의 단계, 화살표 위의 글자가 단계 사이를 오가는 데이터다")
    x, w, cx = 250, 400, 450
    f.box(x, 80, w, 44, None, ["에디터에서 코드 입력"], kind="ui", center=True, size=12.5)
    f.box(700, 72, 276, 60, "pyflakes 정적 분석", ["타이핑할 때마다, 실행 없이 밑줄"], kind="py", size=11.5)
    f.arrow([(650, 102), (700, 102)], "코드", lx=675, ly=94, size=11, dashed=True)
    f.arrow([(cx, 124), (cx, 160)], "실행 ⌘↵ 또는 입력 멈춘 지 2.7초", lx=cx + 10, ly=146, size=11, anchor="start")
    f.box(x, 160, w, 44, None, ["Api.check(code, trigger)  ·  gen += 1"], kind="py", center=True, size=12.5)
    f.arrow([(cx, 204), (cx, 244)], "stdin  {code, pack, repair}", color="#D99A1E", lx=cx + 10, ly=228, size=11, anchor="start")
    f.box(x, 244, w, 150, "harness (서브프로세스)", ["① 문법 검사 → ② solution 로드", "③ 예시 실행 (테스트당 2초)", "④ 히든 테스트: 작은 입력부터, 첫 실패에서 중단",
                                                  "⑤ 최소 반례로 실행 추적", "⑥ 변이 탐색: 한 곳씩 바꿔 모두 통과하는지"], kind="proc", size=11.5)
    f.box(700, 270, 276, 84, "팩 pg42748.json", ["예시 2개 (문제의 입출력 예)", "히든 테스트 340개"], kind="data", size=11.5)
    f.arrow([(700, 312), (654, 312)], "읽기", color="#2E7D4A", lx=677, ly=304, size=11)
    f.arrow([(cx, 394), (cx, 434)], "stdout  {examples, hidden, trace, repair}", color="#D99A1E", lx=cx + 10, ly=418, size=11, anchor="start")
    f.box(x, 434, w, 44, None, ["facts: 실패를 모아 예외 > 오답 > 시간 초과 순으로 정렬"], kind="py", center=True, size=12)
    f.box(700, 434, 276, 44, None, ["테스트 표 · 반례 (즉시 반환)"], kind="ui", center=True, size=12)
    f.arrow([(650, 456), (700, 456)], color="#2C56C9")
    f.arrow([(cx, 478), (cx, 508)], "백그라운드 스레드", lx=cx + 10, ly=497, size=11, anchor="start")
    f.box(x, 508, w, 44, None, ["진단: 규칙 → 변이 탐색 → LLM"], kind="proc", center=True, size=12.5)
    f.arrow([(cx, 552), (cx, 582)], "diag  {tier, line, category, confidence}", lx=cx + 10, ly=571, size=11, anchor="start")
    f.box(x, 582, w, 44, None, ["발화 정책: speak · chip · none"], kind="py", center=True, size=12.5)
    f.arrow([(cx, 626), (cx, 656)], "speak", lx=cx + 10, ly=645, size=11, anchor="start")
    f.box(x, 656, w, 44, None, ["응답 생성 → 유출 검사 → 걸리면 폴백 템플릿"], kind="proc", center=True, size=12.5)
    f.box(700, 656, 276, 44, None, ["말풍선"], kind="ui", center=True, size=12.5)
    f.arrow([(650, 678), (700, 678)], "이벤트", color="#2C56C9", lx=675, ly=670, size=11)
    f.text(24, 734, "이벤트 순서: thinking → line → stream × n → diag → say (또는 chip)", 12, color=MUTED)
    f.save()


if __name__ == "__main__":
    for fn in (overview, check_flow, coach_pipeline, data_flow, attempt_status, build_and_setup, pipeline):
        fn()
    for w in WARN:
        print("경고:", w)
    print(f"그림 7장을 {OUT}에 만들었습니다. 경고 {len(WARN)}개")
