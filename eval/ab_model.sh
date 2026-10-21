#!/bin/bash
# 12B와 e4b를 번갈아 잰다 (속도 3문제씩) + 정확도(2군데 버그 12개)
cd "$(dirname "$0")/.."
B() { .venv/bin/python eval/bench_speed.py "$1" 2>&1 | tail -1; }
unload() { curl -s localhost:11434/api/generate -d "{\"model\":\"$1\",\"keep_alive\":0}" >/dev/null; sleep 2; }
KOTEACHER_MODEL=gemma4:12b-it-qat B 12B-1; unload gemma4:12b-it-qat
KOTEACHER_MODEL=gemma4:e4b-it-qat B e4b-1; unload gemma4:e4b-it-qat
KOTEACHER_MODEL=gemma4:12b-it-qat B 12B-2; unload gemma4:12b-it-qat
KOTEACHER_MODEL=gemma4:e4b-it-qat B e4b-2
echo "--- e4b 정확도 (2군데 버그 12개, 12B 글 형식은 6/12)"
KOTEACHER_MODEL=gemma4:e4b-it-qat .venv/bin/python eval/subset.py llm_r6 e4b_r1 2>&1 | grep -v "^\[" | tail -7
echo "--- e4b 말하기 유출"
KOTEACHER_MODEL=gemma4:e4b-it-qat .venv/bin/python eval/run_eval.py say 10 say_e4b 2>&1 | tail -2
unload gemma4:e4b-it-qat
