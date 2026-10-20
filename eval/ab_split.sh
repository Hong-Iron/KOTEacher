#!/bin/bash
# 같은 12개 버그로 프롬프트 구조 A/B: 예전(한 덩어리) vs 새(대화 나눔)
cd "$(dirname "$0")/.."
KOTEACHER_SPLIT=0 .venv/bin/python eval/subset.py llm_r6 ab_old 2>&1 | grep -v "^\[" | tail -9
KOTEACHER_SPLIT=1 .venv/bin/python eval/subset.py llm_r6 ab_new 2>&1 | grep -v "^\[" | tail -9
