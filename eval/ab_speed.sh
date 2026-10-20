#!/bin/bash
# 속도 후보를 기준과 번갈아 잰다 (발열로 점점 느려지는 영향을 줄이려고)
cd "$(dirname "$0")/.."
B() { .venv/bin/python eval/bench_speed.py "$1" 2>&1 | tail -1; }
B 기준1
KOTEACHER_EXP=textfmt B 형식끔
B 기준2
KOTEACHER_EXP=lean B 원인칸뺌
B 기준3
KOTEACHER_EXP=short B 프롬프트줄임
B 기준4
KOTEACHER_NUM_CTX=4096 B 문맥4k
B 기준5
