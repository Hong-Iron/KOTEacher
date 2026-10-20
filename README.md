# 코테가이드

알고리즘 노트(Obsidian 볼트 `공부/알고리즘/`)와 프로그래머스 90문제로 만드는 로컬 코딩 테스트 연습기.
로컬 gemma4가 문제를 푸는 동안 옆에서 검사하고 질문과 힌트를 준다.

- 설계서: [`docs/design.html`](docs/design.html) (브라우저로 연다)
- 원칙: 맞고 틀림은 테스트 실행이 정한다. gemma4는 확인된 사실을 질문과 힌트로 바꿔 말하는 일만 한다.
- 볼트는 읽기만 한다. 볼트 경로는 설정으로 받는다.

## 로컬 AI

```bash
brew install ollama
brew services start ollama        # FLASH_ATTENTION=1, KV_CACHE_TYPE=q8_0이 기본으로 켜진다
ollama pull gemma4:12b-it-qat     # 7.15GB
```

문맥 길이는 요청마다 `options.num_ctx`로 16384를 넘긴다. 서버 기본값(16GB 맥에서 4K)에 기대지 않는다.

## 폴더

| 폴더 | 내용 |
|---|---|
| `docs/` | 설계서 |
| `prototypes/` | 설계를 확인하려고 만든 일회용 시험 코드. `pipeline_proto.py`는 보석 쇼핑 버그 코드로 반례 줄이기, 실수 지문, 수리 검색을 돌려 본다 (볼트 경로가 박혀 있다) |
