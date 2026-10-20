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


def to_html(s):
    return md.markdown(clean(s), extensions=["tables", "fenced_code", "sane_lists"])


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


def hint_ladder(pid):
    """힌트 사다리 4단계 + 풀이. 각 단계: 제목, HTML, 프롬프트용 글."""
    p = problem(pid)
    s = p["steps"]

    def join(*ks):
        return "\n\n".join(f"**{s[k]['title']}**\n\n{s[k]['md']}" for k in ks if k in s)

    raw = [("필요한 개념", p["need_md"]), ("작은 예로 손으로 풀기", join(1, 2)),
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
