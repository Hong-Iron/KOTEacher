"use strict";
/* 코테가이드 화면. 파이썬 쪽 함수는 window.pywebview.api로 부른다.
   개발 중에는 tools/devserve.py가 같은 함수를 /api/<이름>으로 열어 준다(브라우저 확인용). */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const h = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
const now = () => { const d = new Date(); return `${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`; };

/* ---------------- 파이썬 연결 ---------------- */
let API = null;
function devBridge() {
  const call = name => async (...args) => {
    const r = await fetch(`/api/${name}`, {method: "POST", body: JSON.stringify(args)});
    return r.json();
  };
  const poll = async () => {
    try { const evs = await (await fetch("/events")).json(); evs.forEach(([e, d]) => KG.on(e, d)); } catch (_) {}
    setTimeout(poll, 250);
  };
  poll();
  return new Proxy({}, {get: (_, k) => call(k)});
}
const handlers = {};
window.KG = {on(ev, data) { (handlers[ev] || (() => {}))(data); }};

/* ---------------- 상태 ---------------- */
const S = {problems: [], lv: 0, q: "", p: null, mode: "normal", hints: 0, editor: null, lastChecked: "", checking: false,
  idleTimer: null, saveTimer: null, startT: 0, logN: 0, bubble: null, zoneId: null, zone: null, decos: [], pendingStep: null,
  lastDiag: null};

/* ---------------- 홈 ---------------- */
const STATUS = {solved: "통과", helped: "도움 받음", tried: "시도", new: "새 문제"};
function renderList() {
  const q = S.q.trim();
  const items = S.problems.filter(p => (!S.lv || p.level === S.lv) &&
    (!q || p.title.includes(q) || p.concepts.some(c => c.includes(q)) || (p.source || "").includes(q)));
  const list = $("#plist"); list.innerHTML = "";
  for (const p of items) {
    const r = h("div", "prow");
    r.tabIndex = 0;
    r.innerHTML = `<span class="lv">Lv${p.level}</span><span class="ti">${esc(p.title)}</span><span class="so">${esc(p.source)}</span>
      <span class="co">${esc(p.concepts.join(", "))}</span><span class="pill ${p.status}">${STATUS[p.status]}</span>`;
    r.onclick = () => openProblem(p.id);
    r.onkeydown = e => { if (e.key === "Enter") openProblem(p.id); };
    list.append(r);
  }
  if (!items.length) list.innerHTML = `<p class="note" style="padding:12px 14px;margin:0">맞는 문제가 없다.</p>`;
}
function setAi(st) {
  for (const el of [$("#aiStat"), $("#aiStat2")]) {
    const dot = st.server && st.model ? "on" : st.server ? "wait" : "";
    const txt = st.server && st.model ? `코치 ${st.name.replace(":", " ")} 준비됨` : st.server ? "모델을 받는 중 · 테스트와 수리 검색만 돈다" : "Ollama 꺼짐 · 테스트와 수리 검색만 돈다";
    el.innerHTML = `<span class="dot ${dot}"></span>${esc(txt)}`;
  }
}
async function boot() {
  const b = await API.boot();
  S.problems = b.problems; S.mode = b.mode;
  $("#bookCnt").textContent = b.mistakes;
  setAi(b.ai);
  renderList();
  setInterval(async () => setAi(await API.ai_status()), 15000);
}
$$("#lvSeg button").forEach(b => b.onclick = () => {
  S.lv = +b.dataset.lv; $$("#lvSeg button").forEach(x => x.setAttribute("aria-pressed", x === b)); renderList();
});
$("#search").oninput = e => { S.q = e.target.value; renderList(); };

function show(id) { for (const v of ["home", "solve", "book"]) $("#" + v).hidden = v !== id; if (id === "solve") S.editor?.layout(); }

/* ---------------- Monaco ---------------- */
let monacoReady;
function loadMonaco() {
  if (monacoReady) return monacoReady;
  monacoReady = new Promise(res => {
    require.config({paths: {vs: "vendor/monaco/vs"}});
    window.MonacoEnvironment = {getWorkerUrl: () => "data:text/javascript;charset=utf-8,"};
    require(["vs/editor/editor.main"], () => {
      const base = {"editor.background": "#00000000"};
      monaco.editor.defineTheme("kg-light", {base: "vs", inherit: true, rules: [
        {token: "keyword", foreground: "7a3fb0"}, {token: "number", foreground: "b5530d"}, {token: "string", foreground: "2e7d4a"},
        {token: "comment", foreground: "8a91a0", fontStyle: "italic"}], colors: {"editor.background": "#fbfbfd", "editorLineNumber.foreground": "#a3aab8"}});
      monaco.editor.defineTheme("kg-dark", {base: "vs-dark", inherit: true, rules: [
        {token: "keyword", foreground: "c99cf3"}, {token: "number", foreground: "f3a564"}, {token: "string", foreground: "86d39f"},
        {token: "comment", foreground: "646d7e", fontStyle: "italic"}], colors: {"editor.background": "#13161c", "editorLineNumber.foreground": "#4c5463"}});
      res();
    });
  });
  return monacoReady;
}
const dark = matchMedia("(prefers-color-scheme: dark)");
dark.addEventListener("change", () => window.monaco && monaco.editor.setTheme(dark.matches ? "kg-dark" : "kg-light"));

async function makeEditor(code) {
  await loadMonaco();
  if (!S.editor) {
    S.editor = monaco.editor.create($("#editor"), {
      value: code, language: "python", theme: dark.matches ? "kg-dark" : "kg-light",
      fontFamily: "SF Mono, Menlo, D2Coding, monospace", fontSize: 14, lineHeight: 24, fontLigatures: false,
      minimap: {enabled: false}, glyphMargin: true, scrollBeyondLastLine: false, automaticLayout: true,
      tabSize: 4, insertSpaces: true, renderLineHighlight: "line", padding: {top: 10, bottom: 40},
      quickSuggestions: false, suggestOnTriggerCharacters: false, wordBasedSuggestions: "off", parameterHints: {enabled: false},
    });
    S.editor.onDidChangeModelContent(onEdit);
    S.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => runCheck("run"));
    S.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyB, () => $("#toggleProb").click());
    S.editor.onDidChangeCursorPosition(e => $("#edStat").textContent = `${e.position.lineNumber}번 줄`);
  } else {
    S.editor.setValue(code);
  }
  S.lastChecked = "";
}

function onEdit() {
  clearTimeout(S.idleTimer); clearTimeout(S.saveTimer);
  // 고치기 시작하면 줄 표시는 흐리게 남겨 두고 말풍선은 그대로 둔다
  S.saveTimer = setTimeout(() => API.save_code(S.editor.getValue()), 1500);
  if (S.mode !== "quiet") S.idleTimer = setTimeout(() => runCheck("idle"), 3500);
}

/* ---------------- 말풍선 ---------------- */
function clearBubble() {
  if (S.zoneId != null) S.editor.changeViewZones(a => a.removeZone(S.zoneId));
  S.zoneId = null; S.zone = null;
  S.bubble?.remove(); S.bubble = null;
}
function flagLine(line) {
  S.decos = S.editor.deltaDecorations(S.decos, line ? [{range: new monaco.Range(line, 1, line, 1),
    options: {isWholeLine: true, className: "kg-flag-line", glyphMarginClassName: "kg-flag-glyph"}}] : []);
}
function placeBubble(line, el) {
  clearBubble();
  const ed = S.editor;
  const lines = ed.getModel().getLineCount();
  const after = Math.min(line || 0, lines);
  const info = ed.getLayoutInfo();
  el.style.left = `${info.contentLeft + 8}px`;
  el.style.maxWidth = `${Math.min(580, info.contentWidth - 40)}px`;
  $("#edwrap").append(el);
  S.bubble = el;
  const height = () => el.offsetHeight + 14;
  ed.changeViewZones(a => {
    S.zone = {afterLineNumber: after, heightInPx: height(), domNode: document.createElement("div"),
      onDomNodeTop: top => { el.style.top = `${top + 6}px`; }};
    S.zoneId = a.addZone(S.zone);
  });
  new ResizeObserver(() => {
    if (!S.zone || S.bubble !== el) return;
    S.zone.heightInPx = height();
    ed.changeViewZones(a => a.layoutZone(S.zoneId));
  }).observe(el);
  if (line) ed.revealLineInCenterIfOutsideViewport(line);
}

function bubbleHead(label, sub, closable = true) {
  return `<div class="who">${esc(label)}${sub ? `<span class="sub">· ${esc(sub)}</span>` : ""}${closable ? '<button class="x" data-act="fold" aria-label="접기">×</button>' : ""}</div>`;
}
function evidence(f) {
  if (!f) return "";
  if (f.kind === "wrong") return `${f.where}: ${f.args} → 기대 ${f.expected}, 내 답 ${f.got}`;
  if (f.kind === "error") return `${f.where}: ${f.args} → ${f.msg}`;
  if (f.kind === "timeout") return `${f.where}: ${f.args} → 시간 초과`;
  return "";
}
function bubbleThinking(diag) {
  const el = h("div", "bubble");
  el.innerHTML = bubbleHead("코치", diag?.line ? `${diag.line}번 줄` : "", false) +
    (diag?.fact ? `<div class="evid">${esc(evidence(diag.fact))}</div>` : "") + `<div class="thinking">코치가 보는 중</div>`;
  placeBubble(diag?.line, el);
}
function bubbleSay(d) {
  const el = h("div", "bubble");
  const sub = [d.line ? `${d.line}번 줄` : "", d.diag?.confidence === "확인됨" ? "테스트로 확인됨" : "AI 추정", d.source === "template" ? "정해진 문장" : ""].filter(Boolean).join(" · ");
  el.innerHTML = bubbleHead("코치", sub) + (d.diag?.fact ? `<div class="evid">${esc(evidence(d.diag.fact))}</div>` : "") +
    `<div>${esc(d.message)}</div><div class="acts">
      ${S.hints < 4 ? `<button class="chip pri" data-act="hint">힌트 ${S.hints + 1}단계 열기</button>` : ""}
      <button class="chip" data-act="ask">코치에게 묻기</button>
      <button class="chip ghost" data-act="rate" data-r="good" data-id="${d.id}">도움됨</button>
      <button class="chip ghost" data-act="rate" data-r="bad" data-id="${d.id}">별로</button></div>`;
  placeBubble(d.line, el);
}
function bubbleChip(diag) {
  const el = h("div", "bubble mini");
  el.dataset.act = "explain";
  el.innerHTML = `<span class="d"></span><span>${diag?.fact?.kind === "syntax" ? `문법 오류: ${esc(diag.fact.msg)}` : "코치가 이 줄에 할 말이 있어요"}</span>`;
  placeBubble(diag?.line ?? diag?.fact?.line, el);
}
function bubbleDone(m) {
  const el = h("div", "bubble done");
  const diff = (m.diff || "").split("\n").filter(Boolean).map(l => `<div class="${l[0] === "-" ? "del" : "add"}">${esc(l)}</div>`).join("");
  el.innerHTML = bubbleHead("모두 통과", "오답 기록에 남겼어요") +
    `<div><b class="mname" data-id="${m.id}">${esc(m.name)}</b><span class="cat">${esc(m.category)}</span>
     <span class="note">· ${fmtDur(m.time_to_fix)} · 힌트 ${m.hints_at_detection}개</span></div>
     ${diff ? `<div class="diff">${diff}</div>` : ""}
     <form class="memo" data-id="${m.id}"><input placeholder="왜 틀렸는지 한 줄 (선택)" aria-label="오답 메모"><button class="chip">남기기</button></form>`;
  placeBubble(null, el);
}
function bubblePass() {
  const el = h("div", "bubble done");
  el.innerHTML = bubbleHead("모두 통과", `예시와 숨은 검사 전부`) + `<div>이 문제를 풀었어요. 다른 문제로 가거나, 더 빠른 방법이 있는지 생각해 보세요.</div>`;
  placeBubble(null, el);
}
const fmtDur = s => { s = Math.round(s || 0); return s >= 60 ? `${Math.floor(s / 60)}분 ${s % 60}초` : `${s}초`; };

$("#edwrap").addEventListener("click", async e => {
  const t = e.target.closest("[data-act]"); if (!t) return;
  const act = t.dataset.act;
  if (act === "fold") { const d = S.lastDiag; clearBubble(); if (d) bubbleChip(d); }
  if (act === "explain") { if (S.lastDiag?.fact?.kind === "syntax") return; bubbleThinking(S.lastDiag); API.explain(); }
  if (act === "hint") { $("#main").classList.remove("collapsed"); requestStep(S.hints + 1); }
  if (act === "rate") { API.rate(t.dataset.id, t.dataset.r); t.textContent += " ✓"; }
  if (act === "ask") {
    if (S.bubble.querySelector(".ask")) return;
    const f = h("form", "ask", `<input placeholder="길이가 같은 구간은 어떻게 다뤄야 해?" aria-label="코치에게 물을 말"><button class="chip pri">묻기</button>`);
    S.bubble.append(f); f.querySelector("input").focus();
  }
});
$("#edwrap").addEventListener("submit", async e => {
  e.preventDefault();
  const f = e.target, input = f.querySelector("input"), v = input.value.trim();
  if (f.classList.contains("ask")) {
    if (!v) { input.focus(); return; }
    addLog("me", "나", v);
    f.replaceWith(h("div", "thinking", "코치가 생각하는 중"));
    API.ask(v, S.editor.getValue());
  } else if (f.classList.contains("memo")) {
    if (!v) { input.focus(); return; }
    await API.note(f.dataset.id, v);
    f.replaceWith(h("p", "note", `메모를 남겼어요: “${esc(v)}”`));
    loadMistakes();
  }
});

/* ---------------- 검사 ---------------- */
async function runCheck(trigger) {
  const code = S.editor.getValue();
  if (S.checking || (trigger === "idle" && code === S.lastChecked)) return;
  S.checking = true; $("#run").setAttribute("aria-busy", "true");
  S.lastChecked = code;
  try {
    const r = await API.check(code, trigger);
    renderTests(r);
    monaco.editor.setModelMarkers(S.editor.getModel(), "kg", r.result.syntax ? [{
      startLineNumber: r.result.syntax.line, endLineNumber: r.result.syntax.line, startColumn: 1, endColumn: 200,
      message: r.result.syntax.msg, severity: monaco.MarkerSeverity.Error}] : []);
    $("#out").textContent = r.result.stdout || "print 출력이 없다.";
    if (r.passed) {
      flagLine(null); S.lastDiag = null;
      if (r.mistake) { bubbleDone(r.mistake); addLog("sys", "기록", `오답 기록: ${r.mistake.name}`); loadMistakes(); }
      else if (trigger === "run") bubblePass(); else clearBubble();
      addLog("sys", "테스트", "모두 통과");
      return;
    }
    const d = r.diag;
    if (d && !d.pending) {
      S.lastDiag = d; flagLine(d.line);
      if (r.decision === "chip") bubbleChip(d);
    } else if (d?.pending) {
      S.lastDiag = {fact: d.fact, line: d.fact.line};
    }
    if (r.facts[0] && r.facts[0].kind !== "syntax") addLog("sys", "테스트", evidence(r.facts[0]) || r.facts[0].msg || "실패");
  } catch (err) {
    addLog("sys", "오류", String(err));
  } finally {
    S.checking = false; $("#run").removeAttribute("aria-busy");
  }
}

function renderTests(r) {
  const res = r.result, box = $("#tests"); box.innerHTML = "";
  const cnt = $("#testCnt");
  if (res.fatal || res.syntax || res.load_error) {
    box.innerHTML = `<p class="note" style="color:var(--bad)">${esc(res.fatal || (res.syntax && `${res.syntax.line}번 줄 문법 오류: ${res.syntax.msg}`) || res.load_error)}</p>`;
    cnt.className = "cnt bad"; cnt.textContent = "!"; return;
  }
  const ex = res.examples;
  ex.forEach((e, i) => {
    const s = e.skipped ? `<span class="s skip">–</span>` : e.ok ? `<span class="s ok">✓</span>` : `<span class="s bad">✗</span>`;
    const body = e.ok ? `${esc(e.args)} → <b>${esc(e.got)}</b>` : e.skipped ? `${esc(e.args)} · 앞의 시간 초과로 건너뜀`
      : e.timeout ? `${esc(e.args)} · <b>시간 초과</b>` : e.error ? `${esc(e.args)} · <b>${esc(e.error)}</b>${e.line ? ` (${e.line}번 줄)` : ""}`
      : `${esc(e.args)} 기대 <b>${esc(e.expected)}</b> 내 답 <b>${esc(e.got)}</b>`;
    box.append(h("div", "trow", `${s}<span>예시 ${i + 1}</span><span class="io2" title="${esc(e.args)}">${body}</span><span class="t">${e.ms}ms</span>`));
  });
  const hd = res.hidden;
  if (hd) {
    const ff = hd.first_fail;
    const okAll = !ff && hd.run === hd.total;
    const s = okAll ? `<span class="s ok">✓</span>` : ff ? `<span class="s bad">✗</span>` : `<span class="s skip">–</span>`;
    const body = okAll ? `무작위 ${hd.total}개 모두 일치` : ff ? (ff.timeout ? `가장 작은 반례 ${esc(ff.args)} · <b>시간 초과</b>` : ff.error ? `가장 작은 반례 ${esc(ff.args)} · <b>${esc(ff.error)}</b>` :
      `가장 작은 반례 ${esc(ff.args)} 기대 <b>${esc(ff.expected)}</b> 내 답 <b>${esc(ff.got)}</b> · ${hd.run}번째`) : `${hd.run}/${hd.total}개까지 돌림`;
    box.append(h("div", "trow", `${s}<span>숨은 검사</span><span class="io2" title="${esc(ff?.args || "")}">${body}</span><span class="t">${hd.passed}/${hd.total}</span>`));
  }
  if (r.risk) box.append(h("div", "trow", `<span class="s skip">!</span><span>속도 어림</span><span class="io2">반복문 ${r.risk.depth}겹 × 입력 최대 ${r.risk.n.toLocaleString()} → 연산 약 ${r.risk.ops.toExponential(1)}번. 시간 초과 위험</span><span class="t"></span>`));
  const passedN = ex.filter(e => e.ok).length + (hd && !hd.first_fail && hd.run === hd.total ? 1 : 0);
  cnt.className = "cnt " + (r.passed ? "ok" : "bad"); cnt.textContent = `${passedN} / ${ex.length + 1}`;
}

/* ---------------- 코치 이벤트 ---------------- */
handlers.thinking = () => { if (S.lastDiag && !S.bubble?.classList.contains("done")) bubbleThinking(S.lastDiag); };
handlers.diag = d => { S.lastDiag = d.diag; flagLine(d.diag?.line); };
handlers.chip = d => { S.lastDiag = d.diag; flagLine(d.diag?.line); bubbleChip(d.diag); };
handlers.say = d => { S.lastDiag = d.diag; flagLine(d.line); bubbleSay(d); addLog("ai", "코치", d.message); };
handlers.answer = d => {
  addLog("ai", "코치", d.message);
  const t = S.bubble?.querySelector(".thinking");
  if (t) { t.className = ""; t.textContent = d.message; }
  else { const el = h("div", "bubble"); el.innerHTML = bubbleHead("코치", "질문에 답") + `<div>${esc(d.message)}</div>`; placeBubble(S.lastDiag?.line, el); }
};
handlers.coach_error = d => addLog("sys", "코치 오류", d.error);
handlers.mistake_named = d => { $$(`.mname[data-id="${d.id}"]`).forEach(e => e.textContent = d.name); loadMistakes(); };

function addLog(kind, who, text) {
  const li = h("li", "", `<span class="tm">${now()}</span><span><span class="src ${kind}">${esc(who)}</span>${esc(text)}</span><span></span>`);
  $("#log").append(li); $("#logCnt").textContent = ++S.logN;
  li.scrollIntoView({block: "nearest"});
}

/* ---------------- 힌트 사다리 ---------------- */
function renderLadder(steps) {
  const ol = $("#ladder"); ol.innerHTML = "";
  for (const s of steps) {
    const li = h("li", "rung" + (s.step === 5 ? " final" : ""));
    li.dataset.step = s.step;
    li.innerHTML = `<button><span class="n">${s.step === 5 ? "·" : s.step}</span>${esc(s.title)}<span class="lock">${s.step === 5 ? '기록에 "풀이 봄"' : "열기"}</span></button><div class="body" hidden></div>`;
    li.querySelector("button").onclick = () => requestStep(s.step);
    ol.append(li);
  }
}
function requestStep(step) {
  const next = $$(".rung").find(r => !r.classList.contains("open"));
  if (!next) return;
  if (step < 5) step = Math.min(step, +next.dataset.step);
  if ($(`.rung[data-step="${step}"]`).classList.contains("open")) return;
  if (step === 5 || (step >= 2 && S.hints < 2)) {
    S.pendingStep = step;
    $("#warn span").innerHTML = step === 5 ? "풀이를 보면 이 시도는 <b>오답·풀이 봄</b>으로 기록돼요." : "두 번째 힌트부터는 이 시도가 <b>오답으로 기록</b>돼요.";
    $("#warn").hidden = false; $("#warn").scrollIntoView({block: "nearest"}); return;
  }
  openStep(step);
}
async function openStep(step) {
  const r = await API.hint(step);
  const li = $(`.rung[data-step="${r.step}"]`);
  li.classList.add("open"); li.querySelector(".lock").textContent = "열림";
  const body = li.querySelector(".body"); body.innerHTML = r.html; body.hidden = false;
  S.hints = r.hints; $("#hintMeta").textContent = `힌트 ${S.hints} / 4`;
  addLog("sys", "힌트", `${r.step === 5 ? "풀이" : r.step + "단계"}를 열었다.`);
  li.scrollIntoView({block: "nearest", behavior: "smooth"});
}
$("#warnYes").onclick = () => { $("#warn").hidden = true; if (S.pendingStep) openStep(S.pendingStep); S.pendingStep = null; };
$("#warnNo").onclick = () => { $("#warn").hidden = true; S.pendingStep = null; };

/* ---------------- 오답 기록 ---------------- */
function mistakeRow(m, withTitle) {
  const when = new Date(m.t * 1000);
  const diff = (m.diff || "").split("\n").filter(Boolean).slice(0, 2).map(l => `<code>${esc(l)}</code>`).join(" ");
  return `<div class="mrow"><span><span class="nm">${esc(m.name)}</span><span class="cat">${esc(m.category)}</span>${m.fixed ? "" : '<span class="cat">못 고침</span>'}</span>
    <span class="when">${when.getMonth() + 1}월 ${when.getDate()}일${withTitle ? ` · ${esc(m.title)}` : ""}</span>
    <span class="sub">${esc(m.evidence)}${diff ? "<br>" + diff : ""} · ${fmtDur(m.time_to_fix)} · 힌트 ${m.hints_at_detection}개${m.note ? ` · “${esc(m.note)}”` : ""}</span></div>`;
}
async function loadMistakes() {
  if (!S.p) return;
  const [here, all] = await Promise.all([API.mistakes(S.p.id), API.mistakes(null)]);
  const others = all.filter(m => m.problem_id !== S.p.id).slice(0, 5);
  $("#misCnt").textContent = here.length; $("#misCnt").className = "cnt" + (here.length ? " coach" : "");
  $("#misPanel").innerHTML = `<div class="sect">이 문제</div>` + (here.length ? here.map(m => mistakeRow(m)).join("") :
    `<p class="note" style="margin:4px 0">실패하던 검사를 고치면 여기에 남는다.</p>`) +
    (others.length ? `<div class="sect">최근 다른 문제</div>` + others.map(m => mistakeRow(m, true)).join("") : "");
}
async function openBook() {
  const all = await API.mistakes(null);
  const cats = [...new Set(all.map(m => m.category))];
  const seg = $("#catSeg"); seg.innerHTML = "";
  let cur = "";
  const draw = () => {
    const xs = all.filter(m => !cur || m.category === cur);
    $("#bookList").innerHTML = xs.length ? xs.map(m => `<div class="mcard">${mistakeRow(m, true)}</div>`).join("")
      : `<p class="note">아직 기록이 없다. 문제를 풀다 실패한 검사를 고치면 여기에 쌓인다.</p>`;
  };
  for (const c of ["", ...cats]) {
    const b = h("button", "", c ? `${esc(c)} ${all.filter(m => m.category === c).length}` : `전체 ${all.length}`);
    b.setAttribute("aria-pressed", c === cur);
    b.onclick = () => { cur = c; $$("#catSeg button").forEach(x => x.setAttribute("aria-pressed", x === b)); draw(); };
    seg.append(b);
  }
  draw(); show("book");
}
$("#openBook").onclick = openBook;
$("#bookBack").onclick = () => show("home");

/* ---------------- 문제 열기 ---------------- */
async function openProblem(pid) {
  const p = await API.open(pid);
  S.p = p; S.hints = 0; S.logN = 0; S.lastDiag = null; S.startT = Date.now();
  $("#pTitle").textContent = p.title; $("#pLevel").textContent = `Lv${p.level}`; $("#pSource").textContent = p.source || "연습문제";
  $("#pSource").hidden = !p.source;
  $("#pStatement").innerHTML = p.statement;
  $("#pConcepts").textContent = p.concepts.join(", ");
  $("#pUrl").href = p.url;
  $("#pExamples").innerHTML = `<tr><th>${esc(p.params.join(", "))}</th><th style="width:30%">result</th></tr>` +
    p.examples.map(e => `<tr><td>${esc(e.args)}</td><td>${esc(e.expected)}</td></tr>`).join("");
  renderLadder(p.ladder);
  $("#hintMeta").textContent = "힌트 0 / 4";
  $("#log").innerHTML = ""; $("#logCnt").textContent = "0";
  $("#tests").innerHTML = `<p class="note">실행(⌘↵)하면 예시 ${p.examples.length}개와 숨은 검사 ${p.hidden_total}개를 돌린다.</p>`;
  $("#testCnt").className = "cnt"; $("#testCnt").textContent = "–";
  show("solve");
  await makeEditor(p.code);
  clearBubble(); flagLine(null);
  monaco.editor.setModelMarkers(S.editor.getModel(), "kg", []);
  S.editor.focus();
  loadMistakes();
}
$("#back").onclick = async () => { clearTimeout(S.idleTimer); await API.save_code(S.editor.getValue()); await boot(); show("home"); };

/* ---------------- 기타 조작 ---------------- */
$$("#modeSeg button").forEach(b => b.onclick = () => {
  S.mode = b.dataset.mode; API.set_mode(S.mode);
  $$("#modeSeg button").forEach(x => x.setAttribute("aria-pressed", x === b));
  if (S.mode === "quiet") clearTimeout(S.idleTimer);
});
$("#run").onclick = () => runCheck("run");
$("#toggleProb").onclick = () => { $("#main").classList.toggle("collapsed"); S.editor?.layout(); };
$$(".tabs [role=tab]").forEach(t => t.onclick = () => {
  $$(".tabs [role=tab]").forEach(x => x.setAttribute("aria-selected", x === t));
  $$(".pbody").forEach(p => p.hidden = p.dataset.panel !== t.dataset.tab);
  $("#dock").classList.remove("small"); $("#dockToggle").textContent = "접기";
});
$("#dockToggle").onclick = () => { const s = $("#dock").classList.toggle("small"); $("#dockToggle").textContent = s ? "펼치기" : "접기"; };
setInterval(() => { if (!$("#solve").hidden) { const s = Math.floor((Date.now() - S.startT) / 1000); $("#clock").textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; } }, 1000);

/* ---------------- 시작 ---------------- */
function start() {
  boot().then(() => API.log(`boot ok · 문제 ${S.problems.length}개`)).catch(e => API.log("boot 실패 " + e));
  loadMonaco().then(() => API.log("monaco ok")).catch(e => API.log("monaco 실패 " + e));
  window.addEventListener("error", e => API.log(`JS 오류 ${e.message} @${e.lineno}`));
}
if (window.pywebview?.api) { API = window.pywebview.api; start(); }
else {
  window.addEventListener("pywebviewready", () => { API = window.pywebview.api; start(); });
  setTimeout(() => { if (!API && location.protocol.startsWith("http")) { API = devBridge(); start(); } }, 400);
}
