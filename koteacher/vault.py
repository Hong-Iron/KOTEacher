"""볼트의 풀이 문서와 개념 문서를 읽는다. 볼트에는 쓰지 않는다."""
import functools
import re
from pathlib import Path

import markdown as md

from . import config

WIKI = re.compile(r"!?\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
FOOT = re.compile(r"\[\^[^\]]+\]")
CALLOUT_HEAD = re.compile(r"^> \[!(\w+)\][-+]?\s*(.*)$")


def _front(text):
    if not text.startswith("---"):
        return {}, text
    end = text.index("\n---", 3)
    meta = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[end + 4:]


def clean(s):
    """위키링크는 표시 이름만 남기고, 각주 표시와 그림 삽입은 지운다."""
    s = re.sub(r"!\[\[[^\]]+\]\]", "", s)
    s = WIKI.sub(lambda m: m.group(2) or Path(m.group(1)).name, s)
    return FOOT.sub("", s)


def problem_ids():
    return {p["doc"][:-3]: p["id"] for p in problems()}


def to_html(s):
    from . import render
    return render.render(s, problem_ids())


def plain(s):
    s = clean(s)
    s = re.sub(r"```\w*\n", "", s).replace("```", "")
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    return s.strip()


def _sections(body):
    out, cur, buf = {}, None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if cur:
                out[cur] = "\n".join(buf).strip()
            cur, buf = line[3:].strip(), []
        else:
            buf.append(line)
    if cur:
        out[cur] = "\n".join(buf).strip()
    return out


def _callouts(text):
    """> [!type]- 제목 블록 목록: (type, title, body)"""
    res, cur = [], None
    for line in text.splitlines():
        m = CALLOUT_HEAD.match(line)
        if m:
            cur = [m.group(1), m.group(2).strip(), []]
            res.append(cur)
        elif cur is not None and line.startswith(">"):
            cur[2].append(line[2:] if line.startswith("> ") else line[1:])
        else:
            cur = None
    return [(t, title, "\n".join(b).strip()) for t, title, b in res]


def _concept_links(s):
    return [(Path(p).name, (name or Path(p).name)) for p, name in WIKI.findall(s) if "3.개념집" in p]


@functools.lru_cache(maxsize=None)
def problems():
    items = []
    for f in sorted(config.PRACTICE.glob("[0-9][0-9].*.md")):
        text = f.read_text(encoding="utf-8")
        meta, body = _front(text)
        if not re.fullmatch(r"pg\d+", meta.get("id", "")):
            continue
        head = next((l for l in body.splitlines() if l.startswith("[문제 보기]")), "")
        parts = [p.strip() for p in FOOT.sub("", head).split("·")]
        source = parts[2] if len(parts) > 2 and not parts[2].startswith("정답률") else ""
        url = re.search(r"\((https?://[^)]+)\)", head)
        items.append({
            "id": meta["id"], "title": meta.get("title", f.stem.split(".", 1)[1]),
            "level": int(meta.get("level", 0)), "source": source,
            "url": url.group(1) if url else "", "doc": f.name, "num": f.name[:2],
            "concepts": [name for _, name in _concept_links(meta.get("concepts", ""))],
            "concept_files": [p for p, _ in _concept_links(meta.get("concepts", ""))],
        })
    return items


@functools.lru_cache(maxsize=None)
def problem(pid):
    info = next(p for p in problems() if p["id"] == pid)
    text = (config.PRACTICE / info["doc"]).read_text(encoding="utf-8")
    _, body = _front(text)
    sec = _sections(body)
    steps, need = {}, ""
    for typ, title, b in _callouts(sec.get("풀이", "")):
        m = re.match(r"(\d)단계\s*·\s*(.*)", title)
        if typ == "hint" and "개념" in title:
            need = b
        elif m:
            steps[int(m.group(1))] = {"title": m.group(2), "md": b}
    return {**info, "statement_md": sec.get("문제", ""), "need_md": need, "steps": steps}


HINTS = 3  # 힌트 단계 수. 그 다음 단계가 '풀이 보기'


def hint_ladder(pid):
    """힌트 사다리 3단계 + 풀이. 각 단계: 제목, HTML, 프롬프트용 글.
    '필요한 개념'은 사다리에서 빼고, 문제를 열 때 개념 문서 탭으로 함께 연다."""
    p = problem(pid)
    s = p["steps"]

    def join(*ks):
        return "\n\n".join(f"**{s[k]['title']}**\n\n{s[k]['md']}" for k in ks if k in s)

    raw = [("작은 예로 손으로 풀기", join(1, 2)),
           ("핵심 아이디어", join(3)), ("코드 흐름", join(4)), ("풀이 보기", join(5, 6, 7))]
    return [{"step": i + 1, "title": t, "html": to_html(m), "text": plain(m)} for i, (t, m) in enumerate(raw)]


@functools.lru_cache(maxsize=None)
def concept_brief(filename):
    """개념 문서의 요약과 자주 하는 오해 (프롬프트용, 짧게)."""
    f = config.CONCEPTS / f"{filename}.md"
    if not f.exists():
        return ""
    _, body = _front(f.read_text(encoding="utf-8"))
    summary = next((b for t, _, b in _callouts(body) if t == "summary"), "")
    mis = [f"오해: {title} {b}" for t, title, b in _callouts(_sections(body).get("자주 하는 오해", "")) if t == "misconception"]
    return plain(summary + "\n" + "\n".join(mis))[:900]


@functools.lru_cache(maxsize=None)
def concepts():
    """개념 문서 목록: 번호, 이름, 영어 이름, 요약 첫 문장, 이 개념을 쓰는 문제."""
    use = {}
    for p in problems():
        for f in p["concept_files"]:
            use.setdefault(f, []).append(p["id"])
    items = []
    for f in sorted(config.CONCEPTS.glob("[0-9][0-9].*.md")):
        meta, body = _front(f.read_text(encoding="utf-8"))
        summary = next((b for t, _, b in _callouts(body) if t == "summary"), "")
        first = re.split(r"(?<=[.다])\s", plain(summary), maxsplit=1)[0] if summary else ""
        items.append({"name": f.stem, "num": f.name[:2], "title": meta.get("title", f.stem.split(".", 1)[1]),
                      "aliases": meta.get("aliases", "").strip("[]"), "type": meta.get("type", ""),
                      "summary": first[:120], "problems": use.get(f.stem, [])})
    return items


def concept_doc(name):
    f = config.CONCEPTS / f"{name}.md"
    meta, body = _front(f.read_text(encoding="utf-8"))
    body = re.sub(r"^# .*\n", "", body.lstrip(), count=1)  # 제목은 탭과 머리글에 따로 보인다
    info = next((c for c in concepts() if c["name"] == name), {})
    return {**info, "html": to_html(body)}


@functools.lru_cache(maxsize=None)
def search_index():
    """검색용 글: 개념 문서 본문 전체, 문제는 문제문만 (풀이 단계는 답을 미리 보여 주므로 뺀다)."""
    items = []
    for c in concepts():
        f = config.CONCEPTS / f"{c['name']}.md"
        _, body = _front(f.read_text(encoding="utf-8"))
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        body = re.sub(r"^>\s?\[![^\]]+\][-+]?\s*", "", body, flags=re.M)
        body = re.sub(r"^>\s?", "", body, flags=re.M)
        items.append({"kind": "doc", "key": c["name"], "title": c["title"], "text": plain(body)})
    for p in problems():
        items.append({"kind": "pdoc", "key": p["id"], "title": p["title"], "text": plain(problem(p["id"])["statement_md"])})
    return items


def roadmap():
    f = config.CONTENT / "0.로드맵.md"
    if not f.exists():
        return None
    body = f.read_text(encoding="utf-8")
    body = re.sub(r"^# .*\n", "", body, count=1)
    body = re.sub(r"\s*\(\[\[[^\]]*\.py\\?\|코드\]\]\)", "", body)  # 연습 칸의 '(코드)' 링크는 앱에서 쓰지 않는다
    return to_html(body)
