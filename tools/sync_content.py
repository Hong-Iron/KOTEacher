"""볼트의 알고리즘 개념집·연습문제를 저장소 content/로 옮긴다 (공개용).

    python3 tools/sync_content.py [볼트/알고리즘 경로]

공개 저장소에 올리므로 블로그와 같은 원칙으로 거른다.
- 수업 자료(슬라이드·필기·교수·회차)를 가리키는 보충 각주 줄은 뺀다
- '원본 오류 의심' 상자는 뺀다 (본문에는 이미 바른 내용이 있다)
- '## 내 메모' 절은 뺀다
코드(.py)와 그림(.svg)은 그대로 옮긴다.
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Documents/VAULT/공부/알고리즘"
DST = ROOT / "content"

MENTION = re.compile(
    r"슬라이드|필기|판서|강의\s?자료|강의록|수업\s?자료|수업 중|수업에서|유인물|교수|중앙대|녹음|"
    r"(?<![A-Za-z])pp?\.\s?\d|\d+\s?회\s?(?:강의|슬라이드|자료|차|p\.)|\d+\s?주차|이 강의|자료에(?:는)? 없|자료에서")


def clean_md(text):
    out, skip_warn, skip_memo = [], False, False
    for line in text.split("\n"):
        if re.match(r"^##\s+", line):
            skip_memo = line.strip() == "## 내 메모"
        if skip_memo:
            continue
        head = re.match(r"^>\s*\[!(\w+)\][+-]?\s*(.*)", line)
        if head:
            skip_warn = head.group(1).lower() == "warning" and head.group(2).startswith("원본")
        elif not line.startswith(">"):
            skip_warn = False
        if skip_warn:
            continue
        if re.match(r"^\s*\[\^[^\]]+\]:", line) and MENTION.search(line):
            continue
        out.append(line)
    text = "\n".join(out)
    # 지운 각주를 가리키던 표시도 지운다
    defined = set(re.findall(r"^\s*\[\^([^\]]+)\]:", text, re.M))
    text = re.sub(r"\[\^([^\]]+)\](?!:)", lambda m: m.group(0) if m.group(1) in defined else "", text)
    return text.rstrip() + "\n"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    n = {"md": 0, "py": 0, "svg": 0}
    for sub in ("3.개념집", "4.연습문제"):
        (DST / sub).mkdir(parents=True)
        for f in sorted((SRC / sub).iterdir()):
            if f.suffix == ".md":
                (DST / sub / f.name).write_text(clean_md(f.read_text(encoding="utf-8")), encoding="utf-8")
                n["md"] += 1
            elif f.suffix in (".py", ".svg"):
                shutil.copy2(f, DST / sub / f.name)
                n[f.suffix[1:]] += 1
    # 로드맵: 내부용 '확인할 것' 절과 머리의 진도·시험 줄은 뺀다
    road = (SRC / "0.로드맵.md").read_text(encoding="utf-8")
    road = re.sub(r"^## 확인할 것.*?(?=^## |\Z)", "", road, flags=re.S | re.M)
    road = re.sub(r"^> (시험|진도):.*\n", "", road, flags=re.M)
    # 표의 '상태' 칸(볼트 주인의 숙련도)은 앱 기록과 맞지 않으므로 뺀다
    lines, drop = [], False
    for line in road.split("\n"):
        if line.startswith("|"):
            cells = re.split(r"(?<!\\)\|", line)
            if cells[-2].strip() == "상태":
                drop = True
            if drop:
                line = "|".join(cells[:-2] + [""])
        else:
            drop = False
        lines.append(line)
    road = "\n".join(lines)
    (DST / "0.로드맵.md").write_text(clean_md(road), encoding="utf-8")
    print(f"content/: 문서 {n['md']}, 코드 {n['py']}, 그림 {n['svg']}, 로드맵 1")
    left = [(p.relative_to(DST), l.strip()[:80]) for p in DST.rglob("*.md")
            for l in p.read_text(encoding="utf-8").splitlines() if re.match(r"^\s*\[\^", l) and MENTION.search(l)]
    print("남은 수업 자료 언급:", len(left))


if __name__ == "__main__":
    main()
