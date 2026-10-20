<p align="center"><img src="assets/icon-256.png" width="128" alt=""></p>

<h1 align="center">KOTEacher</h1>
<p align="center"><b>KOTE</b>(코테) + <b>Teacher</b>. 내 컴퓨터에서 도는 AI 코치와 함께 푸는 코딩 테스트 연습 프로그램입니다.</p>

프로그래머스 90문제(Lv1~5, 카카오·PCCP 기출 위주)와 알고리즘 개념 문서 35개가 들어 있습니다. 문제를 풀다 손을 멈추면 테스트가 돌고, 틀린 곳이 있으면 코치가 그 줄 바로 아래에 말풍선으로 질문을 던집니다. 정답을 알려 주지 않고, 스스로 찾게 돕습니다.

- **판정은 테스트가 합니다.** 문제마다 예시와 숨은 검사(무작위 입력 수백 개)를 돌리고, 틀리면 가장 작은 반례를 찾아 보여 줍니다.
- **코치는 질문만 합니다.** 한 군데만 고치면 되는 실수는 AI 없이 바로 찾아 줄을 짚고, 나머지는 gemma4가 실행 추적을 보고 원인 줄을 찾습니다. 답을 흘리지 않도록 걸러 냅니다.
- **모두 내 컴퓨터 안에서 돕니다.** 코드와 질문을 인터넷으로 보내지 않습니다. AI 없이도 문제 풀기, 테스트, 반례 찾기, 개념 문서는 쓸 수 있습니다.

## 설치

### 맥 (가장 쉬운 방법)

1. [Releases](https://github.com/Hong-Iron/KOTEacher/releases)에서 `KOTEacher-*-arm64.dmg`를 받아 열고, KOTEacher를 Applications로 끌어다 놓습니다.
2. 처음 열 때 "확인되지 않은 개발자" 경고가 뜨면 Finder에서 KOTEacher를 **오른쪽 클릭 → 열기 → 열기**를 누릅니다.
3. 앱이 코치 준비를 안내합니다. [Ollama](https://ollama.com/download)를 설치하고, 앱 안의 **모델 받기**를 누르면 됩니다.

애플 실리콘(M1 이후) 맥용입니다. 인텔 맥은 아래 한 줄 설치를 써 주세요.

### 한 줄 설치 (맥, Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/Hong-Iron/KOTEacher/main/install.sh | bash
```

파이썬 확인 → 앱 내려받기(`~/KOTEacher`) → 패키지 설치 → 문제 팩 만들기 → Ollama 설치 → 메모리에 맞는 모델 받기 → 앱 아이콘 만들기를 차례로 합니다. 다시 실행하면 업데이트됩니다.

### 한 줄 설치 (Windows, PowerShell)

```powershell
irm https://raw.githubusercontent.com/Hong-Iron/KOTEacher/main/install.ps1 | iex
```

winget으로 파이썬, git, Ollama를 설치하고 시작 메뉴에 KOTEacher를 넣습니다. 아직 Windows 실기기에서 시험하지 못했습니다. 막히면 이슈로 알려 주세요.

### 직접 설치

```bash
git clone https://github.com/Hong-Iron/KOTEacher.git && cd KOTEacher
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python tools/build_packs.py     # 문제 팩 (약 20초)
.venv/bin/python -m koteacher             # 실행
```

파이썬 3.10 이상이 필요합니다. Linux는 창을 띄우는 데 GTK WebKit이 필요합니다(`sudo apt install python3-gi gir1.2-webkit2-4.1`).

## 코치 모델

| 컴퓨터 메모리 | 모델 | 크기 |
|---|---|---|
| 16GB 이상 | `gemma4:12b-it-qat` | 7.2GB |
| 16GB 미만 | `gemma4:e4b-it-qat` | 6.1GB |

앱이 메모리를 보고 골라 줍니다. 앱을 켜면 모델을 미리 불러오고, 끄면 내립니다(앱이 불러온 경우만).

## 쓰는 법

| 화면 | 하는 일 |
|---|---|
| 문제 | 레벨별 90문제 |
| 로드맵 | 단원별 개념 표. 개념을 누르면 개념 문서, 문제를 누르면 바로 풀기. 문제 옆 점: 초록 통과, 노랑 힌트로 통과, 빨강 시도 |
| 풀기 | 왼쪽 문서 창(문제 + 개념 문서 탭) · 오른쪽 코드 창. 경계선을 끌어 너비를 바꾸고, 양쪽을 접을 수 있습니다 |
| 풀이 기록 | 지난 시도의 코드, 실행 흐름, 코치의 말. 그 코드로 다시 열 수 있습니다 |
| 오답 노트 | 틀렸다가 고친 순간이 자동으로 쌓입니다. 고친 차이, 걸린 시간, 내 메모. 누르면 그 문제로 갑니다 |

- **힌트 사다리**: 작은 예로 손으로 풀기 → 핵심 아이디어 → 코드 흐름 → 풀이 보기. 두 번째 힌트부터 그 시도는 오답으로 기록됩니다.
- **코치 말수**: 조용히(물을 때만) · 보통(테스트로 확인된 문제만 먼저) · 적극(추정과 속도 걱정까지).
- **문서에서 골라 묻기**: 개념 문서나 문제문에서 글을 드래그하면 "코치에게 묻기"가 뜹니다. 물은 곳에는 형광펜이 남고, 문단 아래에 질문과 답이 기록됩니다.

| 단축키 | 동작 |
|---|---|
| ⌘↵ | 실행 |
| ⌘K | 전체 검색 (문제, 개념, 문서 본문, 내 질문, 오답 기록) |
| ⌘B / ⌘⇧B | 문서 창 / 코드 창 접기 |

## 문서와 문제에 대해

- `content/`의 개념 문서와 풀이는 Obsidian 볼트의 알고리즘 노트에서 옮긴 것입니다(블로그 [Studies · 알고리즘](https://hong-iron.github.io/Hongs_Blog/studies/algorithms/)과 같은 내용).
- 문제 설명은 프로그래머스 원문을 줄여 쓴 것이고, 문제의 저작권은 프로그래머스와 출제처에 있습니다. 원문은 각 문제의 링크로 볼 수 있습니다.
- 개념 문서의 수식은 KaTeX, 그림은 Mermaid로 그립니다. 편집기는 Monaco입니다(각 라이선스는 `ui/vendor/`에 있습니다).

## 만드는 사람용

| 파일 | 하는 일 |
|---|---|
| `koteacher/capture.py`, `packs.py` | 풀이 코드의 검사 블록을 돌리며 `solution` 호출(입력, 기준 답)을 기록해 문제 팩을 만듭니다 |
| `koteacher/harness.py`, `runner.py` | 별도 프로세스에서 학생 코드 검사: 예시, 숨은 검사(가장 작은 반례), 수리 검색, 실행 추적 |
| `koteacher/coach.py` | 코치 파이프라인: 사실 → 진단(수리·규칙·AI) → 말하기 → 유출 검사 → 전달 규칙 |
| `koteacher/render.py`, `vault.py` | Obsidian 마크다운(콜아웃, 수식, 위키링크) → 화면 |
| `koteacher/api.py`, `app.py`, `ui/` | 화면과 창 (pywebview, 서버 없음) |
| `eval/` | 코치 평가: 모범 풀이에 버그를 심은 시험지(1군데 258개, 2군데 81개) |
| `tools/sync_content.py` | 볼트 → `content/` (수업 자료 언급과 원본 오류 상자는 뺍니다) |
| `tools/build_mac.py` | 맥 앱과 dmg 만들기 (PyInstaller) |
| `docs/design.html` | 처음 설계서 |

코치 평가 결과(맥북 에어 M3 16GB, gemma4 12B): 한 군데 버그는 AI 없이 94%를 고쳐 버그 줄을 약 96% 맞혔고, 두 군데 버그의 AI 진단은 버그 줄을 77% 맞혔습니다. 답 유출은 0건이었습니다.

맥에서 Ollama를 Homebrew 서비스로 띄울 때는 flash attention과 8비트 캐시가 켜져 프롬프트 읽기가 절반 이하로 느려질 수 있습니다. `tools/ollama.plist`는 그 둘을 끈 실행 설정입니다.
