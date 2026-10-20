"""Obsidian 마크다운을 앱 화면용 HTML로 바꾼다.

- 콜아웃 `> [!type]- 제목` → 접히는 <details> (- 접힘, + 펼침, 없으면 상자)
- 수식 $…$, $$…$$ → 그대로 지켜 두었다가 화면에서 KaTeX로 그린다
- ```mermaid → <pre class="mermaid"> (화면에서 Mermaid로 그린다)
- ![[그림.svg]] → SVG를 문서 안에 넣는다
- [[개념 문서|이름]] → 탭으로 여는 링크, [[문제 풀이|이름]] → 문제 열기 링크, 다른 과목 → 글자만
- 각주, 표
"""
import html
import re
from pathlib import Path

import markdown as md

from . import config

CALLOUT = re.compile(r"^\[!(\w+)\]([-+]?)\s*(.*)$")
WIKI = re.compile(r"(!?)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
LABEL = {"summary": "요약", "definition": "정의", "theorem": "정리", "proof": "증명", "example": "예", "check": "검증",
         "misconception": "자주 하는 오해", "question": "확인 문제", "info": "참고", "hint": "힌트", "warning": "주의",
         "tip": "팁", "note": "메모"}


class Doc:
    def __init__(self, problem_ids):
        self.store = []
        self.problem_ids = problem_ids  # 문서 파일 이름(확장자 없이) → pg id

    def keep(self, html_text):
        self.store.append(html_text)
        return f"KTPH{len(self.store) - 1:05d}X"

    def restore(self, text):
        for _ in range(4):  # 자리표시가 겹쳐 있을 수 있다
            new = re.sub(r"KTPH(\d{5})X", lambda m: self.store[int(m.group(1))], text)
            if new == text:
                break
            text = new
        return text


def _protect_code_and_math(doc, text):
    """코드와 수식을 먼저 떼어 둔다 (마크다운이 _나 *를 건드리지 않게)."""
    out, pos = [], 0
    fence = re.compile(r"^```(\w*)\n(.*?)^```\s*$", re.M | re.S)
    for m in fence.finditer(text):
        out.append(_math(doc, text[pos:m.start()]))
        lang, body = m.group(1), m.group(2)
        if lang == "mermaid":
            out.append("\n\n" + doc.keep(f'<pre class="mermaid">{html.escape(body)}</pre>') + "\n\n")
        else:
            out.append("\n\n" + doc.keep(f'<pre class="code"><code class="lang-{lang}">{html.escape(body.rstrip())}</code></pre>') + "\n\n")
        pos = m.end()
    out.append(_math(doc, text[pos:]))
    return "".join(out)


def _math(doc, text):
    text = re.sub(r"`([^`\n]+)`", lambda m: doc.keep(f"<code>{html.escape(m.group(1))}</code>"), text)
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: doc.keep(f'<div class="math" data-display="1">{html.escape(m.group(1).strip())}</div>'),
                  text, flags=re.S)
    text = re.sub(r"(?<![\\$])\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\d)", lambda m: doc.keep(f'<span class="math">{html.escape(m.group(1))}</span>'), text)
    return text


def _links(doc, text):
    def one(m):
        bang, target, name = m.group(1), m.group(2).rstrip("\\"), m.group(3)  # 표 안에서는 [[경로\|이름]]으로 쓴다
        p = Path(target)
        if bang:
            f = config.CONTENT / p.parent.name / p.name
            if p.suffix == ".svg" and f.exists():
                svg = f.read_text(encoding="utf-8")
                svg = re.sub(r"^<\?xml[^>]*>\s*", "", svg)
                svg = re.sub(r"<!DOCTYPE[^>]*>\s*", "", svg)
                return doc.keep(f'<figure class="fig">{svg}</figure>')
            return ""
        label = html.escape(name or p.name)
        stem = p.name[:-3] if p.name.endswith(".md") else p.name
        if "3.개념집" in target and (config.CONCEPTS / f"{stem}.md").exists():
            return doc.keep(f'<a class="doclink" data-doc="{html.escape(stem)}">{label}</a>')
        if "4.연습문제" in target and stem in doc.problem_ids:
            return doc.keep(f'<a class="doclink prob" data-problem="{doc.problem_ids[stem]}">{label}</a>')
        if p.suffix in (".py", ".svg"):
            return doc.keep(f'<span class="codefile" title="{html.escape(p.name)}">{label}</span>')
        return doc.keep(f'<span class="xlink" title="{html.escape(target)}">{label}</span>')
    return WIKI.sub(one, text)


def _callouts(doc, text):
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        line = lines[i]
        m = CALLOUT.match(line[2:].strip()) if line.startswith(">") else None
        if not m:
            out.append(line)
            i += 1
            continue
        typ, fold, title = m.group(1).lower(), m.group(2), m.group(3)
        body = []
        i += 1
        while i < len(lines) and lines[i].startswith(">"):
            body.append(lines[i][2:] if lines[i].startswith("> ") else lines[i][1:])
            i += 1
        inner = _render_block(doc, "\n".join(body))
        head = _inline(doc, title) if title else LABEL.get(typ, typ)
        if fold:
            out.append(doc.keep(f'<details class="callout c-{typ}"{" open" if fold == "+" else ""}><summary>{head}</summary>'
                                f'<div class="cbody">{inner}</div></details>'))
        else:
            out.append(doc.keep(f'<div class="callout c-{typ}"><div class="ctitle">{head}</div><div class="cbody">{inner}</div></div>'))
        out.append("")
    return "\n".join(out)


def _inline(doc, s):
    s = _links(doc, _math(doc, s))
    h = md.markdown(s)
    return re.sub(r"^<p>(.*)</p>$", r"\1", h.strip(), flags=re.S)


def _render_block(doc, s):
    """콜아웃을 먼저 나누고(안쪽은 다시 이 함수로), 코드·수식을 떼어 두고, 링크를 바꾼 뒤 마크다운으로."""
    s = _callouts(doc, s)
    s = _protect_code_and_math(doc, s)
    s = _links(doc, s)
    h = md.markdown(s, extensions=["tables", "sane_lists", "footnotes"])
    return re.sub(r"<p>\s*(KTPH\d{5}X)\s*</p>", r"\1", h)  # 상자·그림이 <p> 안에 들어가지 않게


def render(text, problem_ids=None):
    """문서 본문(앞머리 제외) → HTML."""
    doc = Doc(problem_ids or {})
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return doc.restore(_render_block(doc, text))
