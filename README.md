# 코테가이드

알고리즘 노트(Obsidian 볼트 `공부/알고리즘/`)와 프로그래머스 90문제로 만든 로컬 코딩 테스트 연습 프로그램.
문제를 푸는 동안 로컬 gemma4가 옆에서 검사하고, 버그 줄 아래 말풍선으로 질문과 힌트를 준다.

- 설계서: [`docs/design.html`](docs/design.html)
- 원칙: 맞고 틀림은 테스트 실행이 정한다. gemma4는 확인된 사실을 질문으로 바꿔 말한다. 볼트는 읽기만 한다. 볼트 경로는 `KOTTE_VAULT`로 바꿀 수 있다.

## 실행

```bash
brew install ollama
# Homebrew 서비스 대신 앱 전용 설정으로 띄운다 (아래 '속도' 참고)
sed "s#\$HOME#$HOME#g" tools/ollama.plist > ~/Library/LaunchAgents/io.github.hong-iron.kotte.ollama.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/io.github.hong-iron.kotte.ollama.plist
ollama pull gemma4:12b-it-qat                        # 7.15GB
python3 -m venv .venv && .venv/bin/pip install pywebview markdown
.venv/bin/python tools/build_packs.py                # 문제 팩 (처음 한 번, 약 20초)
.venv/bin/python tools/make_app.py                   # ~/Applications/코테가이드.app
```

앱은 `~/Applications/코테가이드.app`으로 연다. 개발 중에는 `.venv/bin/python -m kotte`.
맥의 WKWebView 창(pywebview)으로 뜨고, 화면은 파이썬 함수를 직접 부른다. 포트를 여는 서버가 없다.
문맥 길이는 요청마다 `options.num_ctx`로 16384를 넘긴다. 서버 기본값(16GB 맥에서 4K)에 기대지 않는다.

### 속도 (M3, 16GB, gemma4 12B QAT, 1,034토큰 프롬프트로 잼)

| Ollama 설정 | 프롬프트 읽기 | 생성 |
|---|---|---|
| flash attention 끔, KV f16 (이 저장소 설정) | 160~200 tok/s | 10~11 tok/s |
| flash attention 켬, KV f16 | 약 100 tok/s | 약 11 tok/s |
| flash attention 켬, KV q8_0 (Homebrew 서비스 기본값) | 24~110 tok/s | 4~11 tok/s |

gemma4는 슬라이딩 윈도 층이 있어서, 앞부분만 같은 프롬프트는 계산이 재사용되지 않는다(완전히 같을 때만 재사용). 그래서 코치는 프롬프트를 짧게 쓰고, 학생에게 할 말을 JSON의 앞쪽에 두어 먼저 흘려 보낸다.

모델이 없거나 Ollama가 꺼져 있어도 테스트, 반례, 수리 검색, 정해진 문장의 코치는 돈다.

## 구조

| 파일 | 하는 일 |
|---|---|
| `kotte/capture.py` | 볼트 풀이 코드의 검사 블록을 돌리며 `solution` 호출(입력, 기준 답)을 기록 |
| `kotte/packs.py` | 문제 팩 만들기·읽기. 팩은 `~/Library/Application Support/코테가이드/packs/` |
| `kotte/harness.py` | 별도 프로세스에서 내 코드 검사: 예시, 숨은 검사(가장 작은 반례), 수리 검색, 실행 추적 |
| `kotte/runner.py` | harness를 띄우는 쪽 |
| `kotte/vault.py` | 볼트 문서 읽기: 문제문, 힌트 사다리(풀이 1~7단계), 개념 요약 |
| `kotte/coach.py` | 코치 파이프라인: 사실 → 진단(수리·규칙·AI) → 말하기 → 유출 검사 → 전달 규칙 |
| `kotte/ollama.py` | Ollama 클라이언트 (스트리밍, JSON 스키마) |
| `kotte/store.py` | SQLite 기록: 시도, 스냅숏, 코치 발언, 오답 기록 |
| `kotte/api.py` | 화면에서 부르는 함수 |
| `ui/` | 화면 (Monaco 편집기 내장) |
| `design/solve.html` | 풀기 화면 시안 |
| `eval/` | 코치 평가: 모범 풀이에 버그를 심은 시험지와 측정 |
| `tools/devserve.py` | 개발용: 화면을 브라우저에서 확인하는 다리 (127.0.0.1) |
| `prototypes/` | 설계 때 만든 일회용 시험 코드 |

## 코치 평가

```bash
.venv/bin/python eval/bugs.py              # 1군데 버그 258개, 2군데 버그 81개
.venv/bin/python eval/run_eval.py det      # 결정적 단계
.venv/bin/python eval/run_eval.py llm 30   # AI 진단과 말하기
```
