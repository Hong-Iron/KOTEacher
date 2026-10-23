"use strict";
/* KOTEacher 화면. 파이썬 쪽 함수는 window.pywebview.api로 부른다.
   개발 중에는 tools/devserve.py가 같은 함수를 /api/<이름>으로 열어 준다(브라우저 확인용). */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const h = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
// AI가 생각하는 동안 보여 주는 점 세 개 (위아래로 차례로 튄다)
const DOTS = '<span class="bounce" aria-hidden="true"><i></i><i></i><i></i></span>';
const waiting = text => `${esc(text)}${DOTS}`;
const now = () => { const d = new Date(); return `${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`; };

/* ---------------- 파이썬 연결 ---------------- */
let API = null;
function devBridge() {
  const call = name => async (...args) => {
    const r = await fetch(`/api/${name}`, {method: "POST", body: JSON.stringify(args)});
    return r.json();
  };
  const poll = async () => {
    try { const evs = await (await fetch("/events", {method: "POST", cache: "no-store"})).json(); evs.forEach(([e, d]) => KG.on(e, d)); } catch (_) {}
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
  lastDiag: null, exam: false};

/* ---------------- 홈 ---------------- */
const STATUS = {solved: "통과", helped: "힌트로 통과", tried: "시도", new: "새 문제"};
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
  if (!items.length) list.innerHTML = `<p class="note" style="padding:12px 14px;margin:0">맞는 문제가 없습니다.</p>`;
}
// 홈 위쪽: 다시 풀어 볼 문제(지난 코드 없이 빈 틀로) · 다음에 풀 문제
async function renderRecs() {
  const r = await API.recommend(), box = $("#recs");
  const row = (p, retry) => `<button class="rec" data-rec="${p.id}" data-fresh="${retry ? 1 : ""}"><span class="lv">Lv${p.level}</span>
    <span class="ti">${esc(p.title)}</span><span class="why">${esc(p.why)}</span><span class="go">${retry ? "빈 코드로 다시" : "풀기"}</span></button>`;
  const col = (title, sub, xs, retry) => xs.length ? `<div class="rcol"><div class="rhead"><b>${title}</b><span>${sub}</span></div>${xs.map(p => row(p, retry)).join("")}</div>` : "";
  box.innerHTML = col("다시 풀어 볼 문제", "틀렸거나 힌트로 넘긴 문제를 지난 코드 없이", r.retry, true) + col("다음 문제 추천", r.retry.length ? "자주 틀린 개념의 안 푼 문제" : "쉬운 것부터", r.next, false);
  box.hidden = !r.retry.length && !r.next.length;
}
$("#recs").addEventListener("click", e => { const b = e.target.closest("[data-rec]"); if (b) openProblem(b.dataset.rec, null, null, !!b.dataset.fresh); });

function setAi(st) {
  for (const el of [$("#aiStat"), $("#aiStat2")]) {
    const ready = st.server && st.model && st.loaded;
    const dot = ready ? "on" : st.server && st.model ? "wait" : "";
    const txt = st.external ? (ready ? `코치(${st.external} · ${st.name})가 준비되어 있습니다` : "외부 API 설정이 끝나지 않았습니다 · 눌러서 설정합니다")
      : ready ? `코치(${st.name.replace(":", " ")})가 준비되어 있습니다`
      : st.server && st.model ? "코치 모델을 불러오고 있습니다 · 테스트는 지금도 쓸 수 있습니다"
      : st.server ? "코치 모델이 없습니다 · 테스트와 수리 검색은 쓸 수 있습니다" : "Ollama가 꺼져 있습니다 · 테스트와 수리 검색은 쓸 수 있습니다";
    el.innerHTML = `<span class="dot ${dot}"></span>${esc(txt)}`;
  }
}
async function boot() {
  const b = await API.boot();
  S.problems = b.problems; S.mode = b.mode; S.examMin = b.exam_minutes || 0; $("#examTime").value = String(S.examMin); setExam(!!b.exam, false);
  renderRecs();
  $("#bookCnt").textContent = b.mistakes;
  setAi(b.ai);
  renderList();
  // 불러오는 동안은 자주, 준비되면 가끔 확인한다
  if (!S.ticking) {
    S.ticking = true;
    const tick = async () => { try { setAi(await API.ai_status()); } finally { setTimeout(tick, $("#aiStat").querySelector(".dot.on") ? 15000 : 2000); } };
    setTimeout(tick, 2000);
  }
}
$$("#lvSeg button").forEach(b => b.onclick = () => {
  S.lv = +b.dataset.lv; $$("#lvSeg button").forEach(x => x.setAttribute("aria-pressed", x === b)); renderList();
});
$("#search").oninput = e => { S.q = e.target.value; renderList(); };

function show(id) { for (const v of ["home", "solve", "book", "learn", "history"]) $("#" + v).hidden = v !== id; if (id === "solve") S.editor?.layout(); hideAsk(); }

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
      fontFamily: "SF Mono, Menlo, Consolas, D2Coding, monospace", fontSize: 14, lineHeight: 24, fontLigatures: false,
      minimap: {enabled: false}, glyphMargin: true, scrollBeyondLastLine: false, automaticLayout: true,
      tabSize: 4, insertSpaces: true, renderLineHighlight: "line", padding: {top: 10, bottom: 40},
      quickSuggestions: false, suggestOnTriggerCharacters: false, wordBasedSuggestions: "off", parameterHints: {enabled: false},
    });
    S.editor.onDidChangeModelContent(onEdit);
    S.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => runCheck("run"));
    S.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter, () => S.exam && examRun("submit"));
    S.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyB, () => toggleLeft());
    S.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyB, () => toggleRight());
    S.editor.onDidChangeCursorPosition(e => $("#edStat").textContent = `${e.position.lineNumber}번 줄`);
  } else {
    S.editor.setValue(code);
  }
  S.lastChecked = "";
}

// 타이핑 중 정적 검사: 정의되지 않은 이름(빨간 밑줄), 쓰지 않는 import·변수(노란 밑줄). 실전에서는 끈다
async function runLint() {
  if (!S.editor || !S.p) return;
  const model = S.editor.getModel(), code = model.getValue();
  if (S.exam) { monaco.editor.setModelMarkers(model, "lint", []); return; }
  const xs = await API.lint(code);
  if (S.exam || model.getValue() !== code) return;  // 그 사이에 바뀌었으면 버린다
  const sev = {error: monaco.MarkerSeverity.Error, warning: monaco.MarkerSeverity.Warning, info: monaco.MarkerSeverity.Info};
  monaco.editor.setModelMarkers(model, "lint", xs.map(x => ({startLineNumber: x.line, endLineNumber: x.line,
    startColumn: x.col, endColumn: x.end, message: x.msg, severity: sev[x.severity] ?? sev.info, source: "검사"})));
}
function onEdit() {
  clearTimeout(S.idleTimer); clearTimeout(S.saveTimer);
  clearTimeout(S.lintTimer); S.lintTimer = setTimeout(runLint, 400);
  if (S.chip) S.editor.layoutContentWidget(S.chip);  // 줄 끝이 바뀌면 따라간다
  // 고치기 시작하면 줄 표시는 흐리게 남겨 두고 말풍선은 그대로 둔다
  S.saveTimer = setTimeout(() => API.save_code(S.editor.getValue()), 1500);
  if (S.mode !== "quiet" && !S.exam) {
    clearTimeout(S.warmTimer);
    S.warmTimer = setTimeout(() => API.prewarm(S.editor.getValue()), 1200);  // 코치가 읽을 앞부분을 미리 읽혀 둔다
    S.idleTimer = setTimeout(() => runCheck("idle"), 2700);  // 손을 멈춘 뒤 자동 검사까지
  }
}

/* ---------------- 말풍선 ---------------- */
function clearBubble() {
  (S.bubbleSubs || []).forEach(d => d.dispose()); S.bubbleSubs = null;
  if (S.chip) { S.editor.removeContentWidget(S.chip); S.chip = null; }
  if (S.zoneId != null) S.editor.changeViewZones(a => a.removeZone(S.zoneId));
  S.zoneId = null; S.zone = null;
  S.bubble?.remove(); S.bubble = null;
}
function flagLine(line) {
  const ok = line && line <= S.editor.getModel().getLineCount();
  S.decos = S.editor.deltaDecorations(S.decos, ok ? [{range: new monaco.Range(line, 1, line, 1),
    options: {isWholeLine: true, className: "kg-flag-line", glyphMarginClassName: "kg-flag-glyph",
              stickiness: monaco.editor.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges}}] : []);
}
function placeBubble(line, el) {
  clearBubble();
  const ed = S.editor;
  const lines = ed.getModel().getLineCount();
  const after = Math.min(line || 0, lines);
  const info = ed.getLayoutInfo();
  el.style.maxWidth = `${Math.min(580, info.contentWidth - 40)}px`;
  $("#edwrap").append(el);
  S.bubble = el;
  if (!after) {
    // 줄을 모르면 편집기 안 오른쪽 위에 띄운다. 맨 위에 공간을 끼우면 스크롤된 편집기가 그 공간을 화면 위로
    // 밀어내 말풍선이 편집기 밖(상단바 위)으로 나가므로 공간을 끼우지 않는다
    el.classList.add("floating");
    return;
  }
  el.style.left = `${info.contentLeft + 8}px`;
  const height = () => el.offsetHeight + 14;
  // 위치는 스크롤·레이아웃이 바뀔 때마다 직접 계산한다 (Monaco는 스크롤 때 onDomNodeTop을 부르지 않는다).
  // 붙은 줄(과 그 아래 공간)이 화면 밖이면 숨긴다: 상단바·아래 패널 위로 겹치지 않게
  // 붙은 줄은 줄 표시 장식(flagLine)을 따라간다: 위에 줄을 넣거나 지워도 같은 코드 줄에 붙어 있다
  const place = () => {
    if (S.bubble !== el || !S.zone) return;
    const m = ed.getModel(), r = S.decos[0] && m.getDecorationRange(S.decos[0]);
    const ln = Math.min(r ? r.startLineNumber : after, m.getLineCount());
    const y = ed.getBottomForLineNumber(ln) - ed.getScrollTop();
    el.style.top = `${y + 6}px`;
    el.style.visibility = y > -2 && y < ed.getLayoutInfo().height - 24 ? "visible" : "hidden";
  };
  ed.changeViewZones(a => {
    S.zone = {afterLineNumber: after, heightInPx: height(), domNode: document.createElement("div"), onDomNodeTop: place};
    S.zoneId = a.addZone(S.zone);
  });
  S.bubbleSubs = [ed.onDidScrollChange(place), ed.onDidLayoutChange(place), ed.onDidContentSizeChange(place)];
  place();
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
    (diag?.fact ? `<div class="evid">${esc(evidence(diag.fact))}</div>` : "") + `<div class="thinking">${waiting("코치가 살펴보고 있습니다")}</div>`;
  placeBubble(diag?.line, el);
}
function bubbleSay(d) {
  const el = h("div", "bubble");
  const sub = [d.line ? `${d.line}번 줄` : "", d.diag?.confidence === "확인됨" ? "테스트로 확인했습니다" : "AI가 추정했습니다", d.source === "template" ? "정해진 문장" : ""].filter(Boolean).join(" · ");
  const instant = d.source === "instant";
  el.innerHTML = bubbleHead("코치", sub) + (d.diag?.fact ? `<div class="evid">${esc(evidence(d.diag.fact))}</div>` : "") +
    `<div class="msgtext"${instant ? " data-instant" : ""}>${esc(d.message)}</div>${instant ? `<div class="note refining">${waiting("코치가 더 살펴보고 있습니다")}</div>` : ""}<div class="acts">
      ${S.hints < (S.p?.hints_max ?? 3) ? `<button class="chip pri" data-act="hint">힌트 ${S.hints + 1}단계 열기</button>` : ""}
      <button class="chip" data-act="ask">코치에게 묻기</button>
      ${d.id ? `<button class="chip ghost" data-act="rate" data-r="good" data-id="${d.id}">도움이 됐어요</button>
      <button class="chip ghost" data-act="rate" data-r="bad" data-id="${d.id}">별로예요</button>` : ""}</div>`;
  placeBubble(d.line, el);
}
// "할 말이 있어요"는 그 줄의 끝에 붙인다. 줄을 모르면 편집기 맨 위에
function bubbleChip(diag) {
  const line = diag?.line ?? diag?.fact?.line;
  const el = h("div", "bubble mini");
  el.dataset.act = "explain";
  el.innerHTML = `<span class="d"></span><span>${diag?.fact?.kind === "syntax" ? `문법 오류: ${esc(diag.fact.msg)}` : line ? "코치가 이 줄에 할 말이 있어요" : "코치가 할 말이 있어요"}</span>`;
  if (!line) { placeBubble(null, el); return; }
  clearBubble();
  const ed = S.editor;
  el.classList.add("inline");
  // 줄 표시(flagLine 장식)를 따라간다: 위에 줄을 넣거나 지워도, 그 줄을 고쳐 길어져도 끝에 붙어 있다
  const where = () => {
    const m = ed.getModel(), r = S.decos[0] && m.getDecorationRange(S.decos[0]);
    const ln = Math.min(r ? r.startLineNumber : line, m.getLineCount());
    // 줄이 길어 끝에 붙이면 편집기 밖으로 나가면, 그 줄의 오른쪽 끝 안쪽에 둔다
    const info = ed.getLayoutInfo(), cw = info.contentWidth - (el.offsetWidth || 190) - 34;
    const charW = ed.getOption(monaco.editor.EditorOption.fontInfo).typicalHalfwidthCharacterWidth;
    const fit = Math.max(1, Math.floor((cw + ed.getScrollLeft()) / charW) + 1);
    return {lineNumber: ln, column: Math.min(m.getLineMaxColumn(ln), fit)};
  };
  S.chip = {getId: () => "kg.coach.chip", getDomNode: () => el, suppressMouseDown: true,
    getPosition: () => ({position: where(), preference: [monaco.editor.ContentWidgetPositionPreference.EXACT]})};
  ed.addContentWidget(S.chip);
  S.bubble = el;
  ed.revealLineInCenterIfOutsideViewport(line);
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
  if (act === "hint") { setPanes(true, true); activateTab("problem"); requestStep(S.hints + 1); }
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
    f.replaceWith(h("div", "thinking", waiting("코치가 생각하고 있습니다")));
    API.ask(v, S.editor.getValue());
  } else if (f.classList.contains("memo")) {
    if (!v) { input.focus(); return; }
    await API.note(f.dataset.id, v);
    f.replaceWith(h("p", "note", `메모를 남겼어요: “${esc(v)}”`));
    loadMistakes();
  }
});

/* ---------------- 검사 ---------------- */
// 실행 중이라는 것을 분명히 보여 준다. 직접 실행하면 버튼·테스트 탭에, 자동 검사는 아래 상태 줄에만 작게
function showRunning(trigger, btn = $("#run"), what) {
  const t0 = performance.now(), label = btn.textContent;
  if (trigger === "run") {
    btn.setAttribute("aria-busy", "true"); btn.disabled = true; btn.innerHTML = `${btn.id === "submit" ? "제출" : "실행"} 중${DOTS}`;
    $$(".tabs [role=tab]").find(t => t.dataset.tab === "tests")?.click();  // 테스트 탭을 펼쳐 보여 준다
    const n = S.p?.examples.length ?? 0, m = S.p?.hidden_total ?? 0;
    const box = $("#tests"), row = h("div", "running", `${waiting(what || `예시 ${n}개와 숨은 검사 ${m}개를 돌리고 있습니다`)}<span class="el">0.0초</span>`);
    box.prepend(row); box.querySelectorAll(".trow").forEach(r => r.classList.add("stale"));
    const tick = setInterval(() => { const el = row.querySelector(".el"); if (el) el.textContent = `${((performance.now() - t0) / 1000).toFixed(1)}초`; }, 100);
    return () => {
      clearInterval(tick); row.remove();
      btn.removeAttribute("aria-busy"); btn.disabled = false; btn.textContent = label;
      const c = $("#testCnt"); c.classList.remove("flash"); void c.offsetWidth; c.classList.add("flash");
    };
  }
  const st = $("#autoStat"); st.hidden = false; st.innerHTML = waiting("자동 검사 중");
  return () => { st.hidden = true; const c = $("#testCnt"); c.classList.remove("flash"); void c.offsetWidth; c.classList.add("flash"); };
}

async function runCheck(trigger) {
  if (S.exam) { if (trigger === "run") examRun("examples"); return; }
  const code = S.editor.getValue();
  if (S.checking || (trigger === "idle" && code === S.lastChecked)) return;
  S.checking = true;
  S.lastChecked = code;
  const stop = showRunning(trigger);
  try {
    // 검사가 0.1초 만에 끝나도 '실행 중'이 눈에 보이도록 직접 실행은 최소 0.45초 보여 준다
    const [r] = await Promise.all([API.check(code, trigger), trigger === "run" ? new Promise(ok => setTimeout(ok, 450)) : null]);
    renderTests(r);
    monaco.editor.setModelMarkers(S.editor.getModel(), "kg", r.result.syntax && S.exam ? [{
      startLineNumber: r.result.syntax.line, endLineNumber: r.result.syntax.line, startColumn: 1, endColumn: 200,
      message: r.result.syntax.msg, severity: monaco.MarkerSeverity.Error}] : []);
    $("#out").textContent = r.result.stdout || "print 출력이 없습니다.";
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
      if (r.instant) bubbleSay({message: r.instant, line: d.line, diag: d, source: "instant"});
    } else if (d?.pending) {
      S.lastDiag = {fact: d.fact, line: d.fact.line};
    }
    if (r.facts[0] && r.facts[0].kind !== "syntax") addLog("sys", "테스트", evidence(r.facts[0]) || r.facts[0].msg || "실패");
  } catch (err) {
    addLog("sys", "오류", String(err));
  } finally {
    S.checking = false; stop();
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
    const body = e.ok ? `${esc(e.args)} → <b>${esc(e.got)}</b>` : e.skipped ? `${esc(e.args)} · 앞에서 시간 초과가 나서 건너뛰었습니다`
      : e.timeout ? `${esc(e.args)} · <b>시간 초과</b>` : e.error ? `${esc(e.args)} · <b>${esc(e.error)}</b>${e.line ? ` (${e.line}번 줄)` : ""}`
      : `${esc(e.args)} 기대 <b>${esc(e.expected)}</b> 내 답 <b>${esc(e.got)}</b>`;
    box.append(h("div", "trow", `${s}<span>예시 ${i + 1}</span><span class="io2" title="${esc(e.args)}">${body}</span><span class="t">${e.ms}ms</span>`));
  });
  const hd = res.hidden;
  if (hd) {
    const ff = hd.first_fail;
    const okAll = !ff && hd.run === hd.total;
    const s = okAll ? `<span class="s ok">✓</span>` : ff ? `<span class="s bad">✗</span>` : `<span class="s skip">–</span>`;
    const body = okAll ? `무작위 ${hd.total}개가 모두 맞았습니다` : ff ? (ff.timeout ? `가장 작은 반례 ${esc(ff.args)} · <b>시간 초과</b>` : ff.error ? `가장 작은 반례 ${esc(ff.args)} · <b>${esc(ff.error)}</b>` :
      `가장 작은 반례 ${esc(ff.args)} 기대 <b>${esc(ff.expected)}</b> 내 답 <b>${esc(ff.got)}</b> · ${hd.run}번째`) : `${hd.total}개 중 ${hd.run}개까지 돌렸습니다`;
    box.append(h("div", "trow", `${s}<span>숨은 검사</span><span class="io2" title="${esc(ff?.args || "")}">${body}</span><span class="t">${hd.passed}/${hd.total}</span>`));
  }
  if (r.risk) box.append(h("div", "trow", `<span class="s skip">!</span><span>속도 어림</span><span class="io2">반복문 ${r.risk.depth}겹 × 입력 최대 ${r.risk.n.toLocaleString()} → 연산 약 ${r.risk.ops.toExponential(1)}번입니다. 시간 초과가 날 수 있습니다</span><span class="t"></span>`));
  const passedN = ex.filter(e => e.ok).length + (hd && !hd.first_fail && hd.run === hd.total ? 1 : 0);
  cnt.className = "cnt " + (r.passed ? "ok" : "bad"); cnt.textContent = `${passedN} / ${ex.length + 1}`;
}

/* ---------------- 실전 모드 ---------------- */
// 실제 코딩 테스트처럼: 자동 검사·코치·힌트를 끄고, 예시 실행과 제출(통과 개수만)만 쓴다
function setExam(on, save = true) {
  S.exam = on;
  $("#solve").classList.toggle("exam", on);
  $("#examBtn").setAttribute("aria-pressed", on);
  const run = $("#run");
  if (!run.disabled) run.textContent = on ? "예시 실행 ⌘↵" : "실행 ⌘↵";
  run.title = on ? "입출력 예만 돌리기" : "예시와 숨은 검사 돌리기";
  if (save) API.set_exam(on);
  if (!S.p || !S.editor) return;
  startExamTimer();
  runLint();
  if (on) {
    clearTimeout(S.idleTimer); clearTimeout(S.warmTimer);
    clearBubble(); flagLine(null); S.lastDiag = null;
    $("#tests").innerHTML = examIntro();
    $("#testCnt").className = "cnt"; $("#testCnt").textContent = "–";
  } else {
    $("#tests").innerHTML = `<p class="note">실전 모드를 껐습니다. 실행(⌘↵)하면 예시와 숨은 검사를 돌리고, 틀리면 가장 작은 반례와 코치 말을 보여 줍니다.</p>`;
  }
}
const examIntro = () => `<p class="note">실전 모드입니다. 자동 검사, 코치, 힌트가 꺼져 있습니다.
  예시 실행(⌘↵)은 입출력 예 ${S.p.examples.length}개만 돌립니다. 제출(⌘⇧↵)하면 숨은 검사 ${S.p.hidden_total}개를 모두 돌리고, 몇 개를 맞혔는지만 알려 드립니다.</p>`;
$("#examBtn").onclick = () => setExam(!S.exam);
$("#examTime").onchange = e => { S.examMin = +e.target.value; API.set_exam_minutes(S.examMin); startExamTimer(); };
// 문제를 열거나 실전을 켜거나 제한 시간을 바꾸면 지금부터 다시 잰다
function startExamTimer() {
  S.examEnd = S.exam && S.examMin && S.p ? Date.now() + S.examMin * 60000 : null;
  S.examDone = false;
  S.editor?.updateOptions({readOnly: false});
  $("#examOver")?.remove();
}
// 시간이 끝나면 지금 코드로 한 번 제출하고 편집을 막는다
async function timeUp() {
  S.examEnd = null; S.examDone = true;
  $("#clock").textContent = "시간 끝"; $("#clock").classList.add("warn");
  S.editor.updateOptions({readOnly: true});
  while (S.checking) await new Promise(r => setTimeout(r, 200));
  await examRun("submit", {timeup: true, limit: S.examMin});
  const box = h("div", "examover", `<b>제한 시간 ${S.examMin}분이 끝났습니다.</b> 마지막 코드로 제출했고, 편집을 잠갔습니다.
    <div class="acts"><button class="btn" data-over="reveal">실전 끄고 반례 보기</button><button class="btn" data-over="more">시간 넘겨 계속 풀기</button></div>`);
  box.id = "examOver"; $("#tests").prepend(box);
  box.onclick = async e => {
    const k = e.target.closest("[data-over]")?.dataset.over; if (!k) return;
    S.editor.updateOptions({readOnly: false}); box.remove();
    if (k === "reveal") { setExam(false); runCheck("run"); }
    else { await API.exam_overtime(); addLog("sys", "실전", "제한 시간을 넘겨 계속 풉니다. 이제 통과해도 '실전 통과'로 남지 않습니다."); S.editor.focus(); }
  };
}
$("#submit").onclick = () => examRun("submit");

async function examRun(kind, info) {
  if (S.checking) return;
  S.checking = true;
  const code = S.editor.getValue(), sub = kind === "submit";
  const what = sub ? `숨은 검사 ${S.p.hidden_total}개를 모두 돌리고 있습니다` : `예시 ${S.p.examples.length}개를 돌리고 있습니다`;
  const stop = showRunning("run", sub ? $("#submit") : $("#run"), what);
  try {
    const left = S.examEnd ? Math.max(0, Math.round((S.examEnd - Date.now()) / 1000)) : null;
    const [r] = await Promise.all([API.exam_run(code, kind, info || (S.examMin && kind === "submit" ? {limit: S.examMin, left} : null)), new Promise(ok => setTimeout(ok, 450))]);
    if (r.passed && kind === "submit" && S.examEnd) { S.examEnd = null; S.examDone = true; $("#clock").textContent = `통과 · ${mmss(left)} 남김`; }
    renderExam(r);
    const res = r.result;
    monaco.editor.setModelMarkers(S.editor.getModel(), "kg", res.syntax ? [{
      startLineNumber: res.syntax.line, endLineNumber: res.syntax.line, startColumn: 1, endColumn: 200,
      message: res.syntax.msg, severity: monaco.MarkerSeverity.Error}] : []);
    $("#out").textContent = res.stdout || "print 출력이 없습니다.";
    const ex = res.examples || [];
    if (sub && res.submit) addLog("sys", "제출", `숨은 검사 ${res.submit.total}개 중 ${res.submit.passed}개를 맞혔습니다`);
    else if (!sub && ex.length) addLog("sys", "예시 실행", `예시 ${ex.length}개 중 ${ex.filter(e => e.ok).length}개를 맞혔습니다`);
  } catch (err) {
    addLog("sys", "오류", String(err));
  } finally {
    S.checking = false; stop();
  }
}

function renderExam(r) {
  const res = r.result, box = $("#tests"), cnt = $("#testCnt");
  if (res.fatal || res.syntax || res.load_error) { renderTests(r); return; }
  box.innerHTML = "";
  const sub = res.submit;
  if (sub) {
    const score = sub.total ? (100 * sub.passed / sub.total) : 0;
    const parts = [["틀림", sub.wrong], ["시간 초과", sub.timeout], ["오류", sub.error], [sub.stopped === "timeout" ? "시간 초과가 이어져 돌리지 않음" : "시간이 모자라 돌리지 않음", sub.not_run]]
      .filter(([, n]) => n).map(([k, n]) => `${k} ${n}개`).join(" · ");
    const ok = r.passed;
    const el = h("div", "examres", `<div class="big ${ok ? "ok" : "bad"}">${ok ? "통과했습니다" : "통과하지 못했습니다"} · 숨은 검사 ${sub.total}개 중 ${sub.passed}개 (정확성 ${score.toFixed(1)}점)</div>
      <div class="bar"><i style="width:${score}%"></i></div>
      <p class="note" style="margin:0">${parts || "모든 숨은 검사를 맞혔습니다"} · ${sub.sec}초 · 문제를 연 뒤 ${$("#clock").textContent}</p>
      ${ok ? "" : `<div class="acts"><button class="btn" id="examReveal">실전 끄고 반례 보기</button></div>`}`);
    box.append(el);
    el.querySelector("#examReveal")?.addEventListener("click", () => { setExam(false); runCheck("run"); });
    cnt.className = "cnt " + (ok ? "ok" : "bad"); cnt.textContent = `${sub.passed} / ${sub.total}`;
  }
  const ex = res.examples || [];
  ex.forEach((e, i) => {
    const s = e.skipped ? `<span class="s skip">–</span>` : e.ok ? `<span class="s ok">✓</span>` : `<span class="s bad">✗</span>`;
    const body = e.skipped ? `${esc(e.args)} · 앞에서 시간 초과가 나서 건너뛰었습니다` : e.timeout ? `${esc(e.args)} · <b>시간 초과</b>`
      : e.error ? `${esc(e.args)} · <b>${esc(e.error)}</b>${e.line ? ` (${e.line}번 줄)` : ""}`
      : `${esc(e.args)} 기대 <b>${esc(e.expected)}</b> 내 답 <b>${esc(e.got)}</b>`;
    box.append(h("div", "trow", `${s}<span>예시 ${i + 1}</span><span class="io2" title="${esc(e.args)}">${body}</span><span class="t">${e.ms}ms</span>`));
  });
  if (!sub) {
    const n = ex.filter(e => e.ok).length;
    box.append(h("p", "note", n === ex.length ? "예시는 모두 맞았습니다. 제출(⌘⇧↵)해서 숨은 검사로 확인해 보세요." : "예시부터 맞혀 보세요."));
    cnt.className = "cnt " + (n === ex.length ? "ok" : "bad"); cnt.textContent = `${n} / ${ex.length}`;
  }
}

/* ---------------- 코치 이벤트 ---------------- */
// 코치가 살펴보는 동안: 줄을 아직 모르면 말풍선을 띄우지 않고 아래 상태줄에만 알린다.
// AI가 맨 앞에 줄 번호를 쓰는 즉시(line) 그 줄에 띄운다. 말을 아껴 둘 경우(live=false)는 끝까지 상태줄에만
function coachBusy(on) {
  const st = $("#autoStat");
  if (on) { st.hidden = false; st.innerHTML = waiting("코치가 살펴보고 있습니다"); }
  else if (st.textContent.includes("코치")) st.hidden = true;
}
handlers.thinking = d => {
  // 바로 보여 준 문장이 있으면 그대로 두고 AI 문장을 기다린다
  if (S.bubble?.querySelector(".msgtext[data-instant]")) return;
  S.liveThinking = d?.live !== false;
  if (S.lastDiag?.line && S.liveThinking && !S.bubble?.classList.contains("done")) { coachBusy(false); bubbleThinking(S.lastDiag); }
  else coachBusy(true);
};
handlers.line = d => {
  S.lastDiag = {...(S.lastDiag || {}), line: d.line};
  flagLine(d.line);
  if (S.liveThinking && !S.bubble?.querySelector(".msgtext[data-instant]")) { coachBusy(false); bubbleThinking(S.lastDiag); }
};
handlers.diag = d => { coachBusy(false); S.lastDiag = d.diag; flagLine(d.diag?.line); };
handlers.chip = d => { coachBusy(false); S.lastDiag = d.diag; flagLine(d.diag?.line); bubbleChip(d.diag); };
// AI가 줄 칸은 비우고 말에만 "11번 줄"이라고 쓴 경우 그 줄을 쓴다 (코드 안의 줄 번호일 때만)
function lineFromText(t) {
  const m = /(\d+)\s*번\s*줄/.exec(t || ""), n = m && +m[1];
  return n && S.editor && n <= S.editor.getModel().getLineCount() ? n : null;
}
handlers.say = d => {
  coachBusy(false);
  if (!d.line) d.line = lineFromText(d.message);
  S.lastDiag = d.diag ? {...d.diag, line: d.diag.line || d.line} : d.diag;
  flagLine(d.line); bubbleSay(d); addLog("ai", "코치", d.message);
};
handlers.stream = d => {
  // 코치 말이 생성되는 대로 말풍선에 흘려 쓴다
  let el = S.bubble;
  coachBusy(false);
  if (!el || el.classList.contains("done") || el.classList.contains("mini")) { bubbleThinking(S.lastDiag); el = S.bubble; }
  const inst = el.querySelector(".msgtext[data-instant]");
  if (inst) { inst.removeAttribute("data-instant"); inst.textContent = ""; inst.classList.add("live"); }
  // 글이 흘러나오는 동안 끝에 점을 붙여 둔다
  el.querySelector(".refining")?.remove();
  let m = el.querySelector(".live");
  if (!m) { m = h("div", "live"); const t = el.querySelector(".thinking"); t ? t.replaceWith(m) : el.append(m); }
  m.textContent += d.text.replace(/`/g, "");
};
handlers.answer = d => {
  addLog("ai", "코치", d.message);
  const t = S.bubble?.querySelector(".live") || S.bubble?.querySelector(".thinking");
  if (t) { t.className = ""; t.textContent = d.message; }  // 흘려 쓰던 점(.live)도 같이 사라진다
  else { const el = h("div", "bubble"); el.innerHTML = bubbleHead("코치", "질문에 답") + `<div>${esc(d.message)}</div>`; placeBubble(S.lastDiag?.line, el); }
};
handlers.coach_error = d => { coachBusy(false); addLog("sys", "코치 오류", d.error); };
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
    const fin = s.step === steps.length;  // 마지막 단계는 풀이 보기
    const li = h("li", "rung" + (fin ? " final" : ""));
    li.dataset.step = s.step;
    li.innerHTML = `<button><span class="n">${fin ? "·" : s.step}</span>${esc(s.title)}<span class="lock">${fin ? '기록에 "풀이 봄"' : "열기"}</span></button><div class="body" hidden></div>`;
    li.querySelector("button").onclick = () => requestStep(s.step);
    ol.append(li);
  }
}
function requestStep(step) {
  const next = $$(".rung").find(r => !r.classList.contains("open"));
  if (!next) return;
  const FIN = (S.p?.hints_max ?? 3) + 1;
  if (step < FIN) step = Math.min(step, +next.dataset.step);
  if ($(`.rung[data-step="${step}"]`).classList.contains("open")) return;
  if (step === FIN || (step >= 2 && S.hints < 2)) {
    S.pendingStep = step;
    $("#warn span").innerHTML = step === FIN ? "풀이를 보면 이 시도는 <b>오답·풀이 봄</b>으로 기록돼요." : "두 번째 힌트부터는 이 시도가 <b>오답으로 기록</b>돼요.";
    $("#warn").hidden = false; $("#warn").scrollIntoView({block: "nearest"}); return;
  }
  openStep(step);
}
async function openStep(step) {
  const r = await API.hint(step);
  const li = $(`.rung[data-step="${r.step}"]`);
  li.classList.add("open"); li.querySelector(".lock").textContent = "열었습니다";
  const body = li.querySelector(".body"); body.innerHTML = r.html; body.hidden = false;
  S.hints = r.hints; $("#hintMeta").textContent = `힌트 ${S.hints} / ${S.p.hints_max}`;
  addLog("sys", "힌트", `${r.step === S.p.hints_max + 1 ? "풀이" : r.step + "단계"}를 열었습니다.`);
  li.scrollIntoView({block: "nearest", behavior: "smooth"});
}
$("#warnYes").onclick = () => { $("#warn").hidden = true; if (S.pendingStep) openStep(S.pendingStep); S.pendingStep = null; };
$("#warnNo").onclick = () => { $("#warn").hidden = true; S.pendingStep = null; };

/* ---------------- 오답 기록 ---------------- */
function mistakeRow(m, withTitle) {
  const when = new Date(m.t * 1000);
  const diff = (m.diff || "").split("\n").filter(Boolean).slice(0, 2).map(l => `<code>${esc(l)}</code>`).join(" ");
  return `<div class="mrow" data-pid="${m.problem_id}" title="이 문제 열기"><span><span class="nm">${esc(m.name)}</span><span class="cat">${esc(m.category)}</span>${m.fixed ? "" : '<span class="cat">고치지 못했습니다</span>'}</span>
    <span class="when">${when.getMonth() + 1}월 ${when.getDate()}일${withTitle ? ` · ${esc(m.title)}` : ""}<button class="chip retry" data-retry="${m.problem_id}" title="지난 코드 없이 빈 틀로 이 문제를 다시 엽니다">다시 풀기</button></span>
    <span class="sub">${esc(m.evidence)}${diff ? "<br>" + diff : ""} · ${fmtDur(m.time_to_fix)} · 힌트 ${m.hints_at_detection}개${m.note ? ` · “${esc(m.note)}”` : ""}</span></div>`;
}
async function loadMistakes() {
  if (!S.p) return;
  const [here, all] = await Promise.all([API.mistakes(S.p.id), API.mistakes(null)]);
  const others = all.filter(m => m.problem_id !== S.p.id).slice(0, 5);
  $("#misCnt").textContent = here.length; $("#misCnt").className = "cnt" + (here.length ? " coach" : "");
  $("#misPanel").innerHTML = `<div class="sect">이 문제</div>` + (here.length ? here.map(m => mistakeRow(m)).join("") :
    `<p class="note" style="margin:4px 0">실패하던 검사를 고치면 여기에 남습니다.</p>`) +
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
      : `<p class="note">아직 기록이 없습니다. 문제를 풀다 실패한 검사를 고치면 여기에 쌓입니다.</p>`;
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
// 오답 기록의 '다시 풀기': 빈 틀로 다시 연다
document.addEventListener("click", e => {
  const b = e.target.closest("[data-retry]"); if (!b) return;
  e.stopPropagation(); openProblem(b.dataset.retry, null, null, true);
});
// 오답 기록(오답 노트, 풀기 화면의 탭)을 누르면 그 문제를 연다
document.addEventListener("click", e => {
  const row = e.target.closest(".mrow[data-pid]");
  if (!row || e.target.closest("a, button, input")) return;
  if (S.p && row.dataset.pid === S.p.id && !$("#solve").hidden) return;  // 지금 푸는 문제면 그대로
  openProblem(row.dataset.pid);
});
$("#bookBack").onclick = () => show("home");

/* ---------------- 문제 열기 ---------------- */
async function openProblem(pid, withDoc, code, fresh = false) {
  const p = await API.open(pid, code || null, fresh);
  S.p = p; S.hints = 0; S.logN = 0; S.lastDiag = null; S.startT = Date.now();
  $("#pTitle").textContent = p.title; $("#pLevel").textContent = `Lv${p.level}`; $("#pSource").textContent = p.source || "연습문제";
  $("#pSource").hidden = !p.source;
  $("#pStatement").innerHTML = p.statement;
  $("#pConcepts").innerHTML = p.concept_files.map((f, i) => `<button data-doc="${esc(f)}" title="문서 창에 탭으로 열기">${esc(p.concepts[i])}</button>`).join("");
  $("#pUrl").href = p.url;
  $("#pExamples").innerHTML = `<tr><th>${esc(p.params.join(", "))}</th><th style="width:30%">result</th></tr>` +
    p.examples.map(e => `<tr><td>${esc(e.args)}</td><td>${esc(e.expected)}</td></tr>`).join("");
  renderLadder(p.ladder);
  $("#hintMeta").textContent = `힌트 0 / ${p.hints_max}`;
  $("#log").innerHTML = ""; $("#logCnt").textContent = "0";
  $("#tests").innerHTML = S.exam ? examIntro() : `<p class="note">실행(⌘↵)하면 예시 ${p.examples.length}개와 숨은 검사 ${p.hidden_total}개를 돌립니다.</p>`;
  $("#testCnt").className = "cnt"; $("#testCnt").textContent = "–";
  show("solve");
  activateTab("problem");
  decorate($('#dbody > .dpanel[data-tab="problem"]')).then(() => applyNotes($('#dbody > .dpanel[data-tab="problem"]')));
  if (withDoc) openDoc(withDoc, false);
  activateTab("problem");
  if (S.editor) { clearBubble(); flagLine(null); coachBusy(false); }
  await makeEditor(p.code);
  startExamTimer();
  runLint();
  clearBubble(); flagLine(null);
  monaco.editor.setModelMarkers(S.editor.getModel(), "kg", []);
  S.editor.focus();
  loadMistakes();
  loadProblemHistory();
}
$("#back").onclick = async () => { clearTimeout(S.idleTimer); await API.save_code(S.editor.getValue()); await boot(); show("home"); };

/* ---------------- 기타 조작 ---------------- */
$$("#modeSeg button").forEach(b => b.onclick = () => {
  S.mode = b.dataset.mode; API.set_mode(S.mode);
  $$("#modeSeg button").forEach(x => x.setAttribute("aria-pressed", x === b));
  if (S.mode === "quiet") clearTimeout(S.idleTimer);
});
$("#run").onclick = () => runCheck("run");
// 처음부터: 지금 코드를 풀이 기록에 저장하고, 빈 틀로 새 시도를 연다 (힌트·코치 기록·제한 시간도 새로)
$("#resetCode").onclick = async () => {
  if (!S.p || !S.editor) return;
  const saved = await API.save_before_reset(S.editor.getValue());
  await openProblem(S.p.id, null, null, true);
  addLog("sys", "처음부터", saved ? "이전 코드는 풀이 기록에 저장했습니다. '풀이 기록' 탭에서 다시 불러올 수 있습니다." : "빈 틀로 다시 시작했습니다.");
  loadProblemHistory();
};

$$(".tabs [role=tab]").forEach(t => t.onclick = () => {
  $$(".tabs [role=tab]").forEach(x => x.setAttribute("aria-selected", x === t));
  $$(".pbody").forEach(p => p.hidden = p.dataset.panel !== t.dataset.tab);
  $("#dock").classList.remove("small"); $("#dockToggle").textContent = "접기";
});
$("#dockToggle").onclick = () => { const s = $("#dock").classList.toggle("small"); $("#dockToggle").textContent = s ? "펼치기" : "접기"; };
const mmss = s => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
setInterval(() => {
  if ($("#solve").hidden) return;
  const c = $("#clock");
  if (S.exam && S.examEnd) {  // 실전 제한 시간: 남은 시간, 5분 아래면 빨갛게
    const left = Math.max(0, Math.ceil((S.examEnd - Date.now()) / 1000));
    c.textContent = `남은 ${mmss(left)}`; c.classList.toggle("warn", left <= 300); c.classList.add("timer");
    if (!left) timeUp();
  } else {
    c.classList.remove("warn", "timer");
    if (!S.examDone) c.textContent = mmss(Math.floor((Date.now() - S.startT) / 1000));
  }
}, 1000);


/* ---------------- 홈: 문제 / 개념 목록 ---------------- */
S.list = "problems"; S.concepts = [];
$$("#homeSeg button").forEach(b => b.onclick = async () => {
  S.list = b.dataset.list; $$("#homeSeg button").forEach(x => x.setAttribute("aria-pressed", x === b));
  $("#plist").hidden = S.list !== "problems"; $("#clist").hidden = S.list !== "concepts"; $("#lvSeg").hidden = S.list !== "problems";
  $("#search").hidden = S.list !== "problems";
  if (S.list === "concepts") await renderRoadmap();
});
// 블로그 로드맵처럼: 단원마다 읽기 전에 · 개념 표 · 떠올려 보기, 끝에 흐름 그림. 문제 옆에는 내 풀이 상태 점
async function renderRoadmap() {
  const r = await API.roadmap(), box = $("#clist");
  box.innerHTML = `<header class="rm-head"><div class="rm-eyebrow">로드맵</div><h1>알고리즘 로드맵</h1>
    <div class="rm-stats"><span><b>개념</b> ${r.concepts}</span><span><b>문제</b> ${r.problems}</span><span><b>통과</b> ${r.solved}</span><span><b>힌트로 통과</b> ${r.helped}</span></div></header>` + r.html;
  $$("a[data-problem]", box).forEach(a => { const st = r.status[a.dataset.problem]; if (st) a.dataset.status = st; });
  await decorate(box);
}
function renderConcepts() {
  const q = S.q.trim(), box = $("#clist"); box.innerHTML = "";
  const items = S.concepts.filter(c => !q || c.title.includes(q) || c.aliases.toLowerCase().includes(q.toLowerCase()));
  for (const c of items) {
    const r = h("div", "crow");
    r.tabIndex = 0;
    r.innerHTML = `<span class="num">${c.num}</span><span class="ti">${esc(c.title)}<span class="al">${esc(c.aliases.split(",")[0] || "")}</span></span>
      <span class="pc">${c.problems.length ? `문제 ${c.solved}/${c.problems.length}` : "수학 연결"}</span><span class="su">${esc(c.summary)}</span>`;
    r.onclick = () => openConcept(c.name);
    r.onkeydown = e => { if (e.key === "Enter") openConcept(c.name); };
    box.append(r);
  }
}
$("#search").addEventListener("input", () => { if (S.list === "concepts") renderConcepts(); });

/* ---------------- 문서 그리기 (수식, Mermaid) ---------------- */
let mermaidReady = false;
async function decorate(el) {
  $$(".math", el).forEach(m => {
    if (m.dataset.done) return;
    try { katex.render(m.textContent, m, {displayMode: !!m.dataset.display, throwOnError: false}); } catch (_) {}
    m.dataset.done = 1;
  });
  const ms = $$("pre.mermaid:not([data-processed])", el);
  if (ms.length && window.mermaid) {
    if (!mermaidReady) { mermaid.initialize({startOnLoad: false, theme: dark.matches ? "dark" : "default", securityLevel: "strict"}); mermaidReady = true; }
    try { await mermaid.run({nodes: ms}); } catch (e) { API.log("mermaid " + e); }
  }
}

/* ---------------- 문서 창 탭 ---------------- */
S.tabs = [{key: "problem", title: "문제"}]; S.active = "problem";
function renderTabs() {
  const bar = $("#dtabs"); bar.innerHTML = "";
  for (const t of S.tabs) {
    const b = h("div", "dtab");
    b.setAttribute("role", "tab"); b.setAttribute("aria-selected", t.key === S.active); b.tabIndex = 0;
    b.innerHTML = t.key === "problem" ? `<span class="t">문제</span>` : `<span class="k">${esc(t.num)}</span><span class="t">${esc(t.title)}</span><button class="x" aria-label="${esc(t.title)} 닫기">×</button>`;
    if (t.key.startsWith("code:")) b.classList.add("code");
    b.onclick = e => { if (e.target.classList.contains("x")) closeTab(t.key); else activateTab(t.key); };
    b.onauxclick = e => { if (e.button === 1 && t.key !== "problem") closeTab(t.key); };
    bar.append(b);
  }
  $(`.dtab[aria-selected="true"]`)?.scrollIntoView({block: "nearest", inline: "nearest"});
}
function activateTab(key) {
  S.active = key;
  $$("#dbody > .dpanel").forEach(p => p.hidden = p.dataset.tab !== key);
  renderTabs();
}
async function openDoc(name, activate = true, auto = false) {
  setPanes(true, S.rightOn ?? true);
  const key = "doc:" + name;
  if (!S.tabs.find(t => t.key === key)) {
    const d = await API.concept(name);
    S.tabs.push({key, title: d.title, num: d.num, auto});
    const panel = h("div", "dpanel doc");
    panel.dataset.tab = key; panel.dataset.doc = name; panel.hidden = true;
    panel.innerHTML = `<h1>${esc(d.title)}</h1>` + d.html;
    $("#dbody").append(panel);
    decorate(panel).then(() => applyNotes(panel));
  }
  else if (!auto) S.tabs.find(t => t.key === key).auto = false;  // 직접 열면 자동 탭이 아니게 된다
  if (activate) activateTab(key); else renderTabs();
}
function closeTab(key) {
  const i = S.tabs.findIndex(t => t.key === key);
  if (i <= 0) return;
  S.tabs.splice(i, 1);
  $(`#dbody > .dpanel[data-tab="${CSS.escape(key)}"]`)?.remove();
  if (S.active === key) activateTab(S.tabs[Math.max(0, i - 1)].key); else renderTabs();
}
renderTabs();

// 문서 속 링크: 개념은 탭으로, 문제는 그 문제를 연다
document.addEventListener("click", e => {
  const a = e.target.closest("[data-doc], [data-problem], [data-code]");
  // 문서 본문 상자(#lDoc, 문서 탭)도 data-doc을 갖는다. 본문을 누르거나 드래그한 것은 링크가 아니다
  if (!a || a.closest(".crow") || a.id === "lDoc" || a.classList.contains("dpanel")) return;
  e.preventDefault();
  if (a.dataset.code) openCode(a.dataset.code);
  else if (a.dataset.problem) openProblem(a.dataset.problem);
  else if (!$("#learn").hidden || !$("#home").hidden) openConcept(a.dataset.doc);
  else openDoc(a.dataset.doc);
});

/* ---------------- 창 접기와 너비 ---------------- */
function setPanes(left, right) {
  if (!left && !right) right = true;   // 둘 다 접을 수는 없다
  S.leftOn = left; S.rightOn = right;
  const sp = $("#split");
  sp.classList.toggle("left-off", !left); sp.classList.toggle("right-off", !right);
  $("#railLeft").hidden = left; $("#railRight").hidden = right;
  $("#foldLeft").setAttribute("aria-pressed", left); $("#foldRight").setAttribute("aria-pressed", right);
  S.editor?.layout();
}
const toggleLeft = () => setPanes(!(S.leftOn ?? true), S.rightOn ?? true);
const toggleRight = () => setPanes(S.leftOn ?? true, !(S.rightOn ?? true));
$("#foldLeft").onclick = toggleLeft; $("#foldRight").onclick = toggleRight;
$("#railLeft").onclick = () => setPanes(true, S.rightOn ?? true);
$("#railRight").onclick = () => setPanes(S.leftOn ?? true, true);
document.addEventListener("keydown", e => {
  if ($("#solve").hidden || !(e.metaKey || e.ctrlKey) || e.key.toLowerCase() !== "b") return;
  if (document.activeElement?.closest("#editor")) return;  // 편집기 안에서는 Monaco 명령이 받는다
  e.preventDefault(); e.shiftKey ? toggleRight() : toggleLeft();
});
(function splitter() {
  const sp = $("#splitter"), split = $("#split");
  try { const w = localStorage.getItem("kt-left-w"); if (w) split.style.setProperty("--left-w", w); } catch (_) {}
  const setW = px => {
    const total = split.getBoundingClientRect().width;
    const w = Math.round(Math.min(Math.max(px, 260), total - 320) / total * 1000) / 10 + "%";
    split.style.setProperty("--left-w", w);
    try { localStorage.setItem("kt-left-w", w); } catch (_) {}
    S.editor?.layout();
  };
  sp.addEventListener("pointerdown", e => {
    sp.setPointerCapture(e.pointerId); sp.classList.add("drag");
    const left = split.getBoundingClientRect().left;
    const move = ev => setW(ev.clientX - left);
    const up = () => { sp.classList.remove("drag"); sp.removeEventListener("pointermove", move); sp.removeEventListener("pointerup", up); };
    sp.addEventListener("pointermove", move); sp.addEventListener("pointerup", up);
  });
  sp.addEventListener("keydown", e => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    setW($("#leftPane").getBoundingClientRect().width + (e.key === "ArrowLeft" ? -40 : 40));
  });
  sp.addEventListener("dblclick", () => { split.style.removeProperty("--left-w"); try { localStorage.removeItem("kt-left-w"); } catch (_) {} S.editor?.layout(); });
})();

/* ---------------- 학습 화면 ---------------- */
async function openConcept(name) {
  const d = await API.concept(name);
  S.learnDoc = name;
  $("#lTitle").textContent = d.title; $("#lAlias").textContent = d.aliases.split(",")[0] || ""; $("#lAlias").hidden = !d.aliases;
  const box = $("#lDoc"); box.innerHTML = d.html; box.dataset.doc = name; box.scrollTop = 0;
  $("#lProblems").innerHTML = d.problem_list.length ? d.problem_list.map(p =>
    `<div class="lp" data-pid="${p.id}" tabindex="0"><span class="lv">Lv${p.level}</span><span class="ti">${esc(p.title)}</span><span class="pill ${p.status}">${STATUS[p.status]}</span></div>`).join("")
    : `<p class="note">이 문서는 수학 과목과 잇는 문서라 바로 풀 문제가 없습니다.</p>`;
  $$(".lp").forEach(el => el.onclick = () => openProblem(el.dataset.pid, name));
  show("learn");
  decorate(box).then(() => applyNotes(box));
}
$("#learnBack").onclick = () => show("home");

/* ---------------- 문서에서 골라 묻기 ---------------- */
const askBtn = h("button", "askbtn", "코치에게 묻기");
const askBox = h("div", "askbox");
askBtn.hidden = askBox.hidden = true;
document.body.append(askBtn, askBox);
let askSel = null, askSeq = 0;
function hideAsk() { askBtn.hidden = true; askBox.hidden = true; }
// 문서 안의 글자 지도: 공백을 뺀 글자마다 (텍스트 노드, 위치). 기록 상자와 묻기 창은 뺀다.
function textMap(host) {
  const pos = []; let str = "";
  const walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT, {acceptNode: n =>
    n.parentElement.closest(".qa-note, .askbox, .katex-mathml, script, style") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  for (let n; (n = walker.nextNode());) {
    const t = n.nodeValue;
    for (let i = 0; i < t.length; i++) if (!/\s/.test(t[i])) { str += t[i]; pos.push([n, i]); }
  }
  return {str, pos};
}
const squash = t => t.replace(/\s+/g, "");
function docKeyOf(host) {
  if (host.id === "lDoc") return host.dataset.doc;
  if (host.dataset.doc) return host.dataset.doc;
  if (host.dataset.tab === "problem" && S.p) return "problem:" + S.p.id;
  return null;
}
// 코드 블록의 글: 줄바꿈(<br>)을 살리고 질문 기록은 뺀다
function codeText(pre, upTo) {
  const r = document.createRange(); r.selectNodeContents(pre);
  if (upTo) r.setEnd(upTo.startContainer, upTo.startOffset);
  const frag = r.cloneContents();
  frag.querySelectorAll(".qa-note").forEach(n => n.remove());
  frag.querySelectorAll("br").forEach(b => b.replaceWith("\n"));
  return frag.textContent;
}
// 고른 줄 앞뒤 12줄을 줄 번호와 함께 (코드 파일 전체를 보내지 않는다)
function codeContext(pre, range) {
  const lines = codeText(pre).split("\n"), at = codeText(pre, range).split("\n").length - 1;
  const a = Math.max(0, at - 12), b = Math.min(lines.length, at + 13);
  return `(코드 ${lines.length}줄 가운데 ${a + 1}~${b}번 줄, 고른 곳은 ${at + 1}번 줄)\n` +
    lines.slice(a, b).map((l, i) => `${String(a + i + 1).padStart(3)}| ${l}`).join("\n");
}
function selectionInDoc() {
  const sel = getSelection();
  if (!sel || sel.isCollapsed || !sel.rangeCount) return null;
  const text = sel.toString().trim();
  if (squash(text).length < 2) return null;
  const range = sel.getRangeAt(0);
  const el = n => n.nodeType === 1 ? n : n.parentElement;
  const host = el(range.startContainer).closest(".dpanel, #lDoc");
  if (!host || host !== el(range.endContainer).closest(".dpanel, #lDoc") || el(range.startContainer).closest(".qa-note")) return null;
  const doc = docKeyOf(host); if (!doc) return null;
  const {str, pos} = textMap(host);
  const start = pos.findIndex(([n, o]) => range.comparePoint(n, o) >= 0);
  const block = el(range.startContainer).closest("p, li, td, .cbody, pre, h2, h3") || host;
  const context = block.tagName === "PRE" ? codeContext(block, range) : block.innerText.slice(0, 1500);
  return {text: text.slice(0, 1200), context, doc, host,
          prefix: start > 0 ? str.slice(Math.max(0, start - 30), start) : "", rect: range.getBoundingClientRect()};
}
document.addEventListener("mouseup", e => {
  if (e.target.closest?.(".askbox, .askbtn")) return;
  setTimeout(() => {
    const s = selectionInDoc();
    if (!s) { if (askBox.hidden) hideAsk(); return; }
    askSel = s;
    askBtn.style.left = `${Math.min(innerWidth - 130, s.rect.left + s.rect.width / 2 - 50)}px`;
    askBtn.style.top = `${Math.max(8, s.rect.top - 36)}px`;
    askBtn.hidden = false;
  }, 0);
});
document.addEventListener("keydown", e => { if (e.key === "Escape") hideAsk(); });
askBtn.addEventListener("mousedown", e => e.preventDefault());
askBtn.onclick = () => {
  const s = askSel; if (!s) return;
  askBtn.hidden = true;
  askBox.innerHTML = `<div class="who">고른 부분에 대해 묻기<button class="x" aria-label="닫기">×</button></div>
    <blockquote>${esc(s.text.length > 160 ? s.text.slice(0, 160) + "…" : s.text)}</blockquote>
    <div class="quick"><button data-q="이게 무슨 뜻인지 쉬운 말로 설명해 줘">쉽게 설명</button><button data-q="작은 예를 하나 들어 줘">예를 들어 줘</button><button data-q="왜 그런지 이유를 알려 줘">왜 그래?</button></div>
    <form class="ask"><input placeholder="이 부분에서 궁금한 것" aria-label="질문"><button class="chip pri">묻기</button></form>`;
  const r = s.rect, w = 380;
  askBox.style.left = `${Math.max(8, Math.min(innerWidth - w - 8, r.left))}px`;
  askBox.style.top = `${Math.min(innerHeight - 220, r.bottom + 8)}px`;
  askBox.hidden = false;
  askBox.querySelector("input").focus();
  const send = q => {
    // 묻는 순간 원문에 표시하고, 문단 아래 기록 상자에 답을 흘려 쓴다
    const id = ++askSeq;
    hideAsk(); getSelection().removeAllRanges();
    const note = {id: "tmp" + id, quote: s.text, prefix: s.prefix, question: q, answer: ""};
    const box = placeNote(s.host, note, true);
    if (box) { box.querySelector(".qa").classList.add("thinking"); box.querySelector(".qa").innerHTML = waiting("코치가 생각하고 있습니다"); box.dataset.rid = id; }
    API.ask_doc(id, s.text, s.context, s.doc, q, s.prefix, S.editor && !$("#solve").hidden ? S.editor.getValue() : "");
  };
  askBox.querySelector(".x").onclick = hideAsk;
  askBox.querySelectorAll(".quick button").forEach(b => b.onclick = () => send(b.dataset.q));
  askBox.querySelector("form").onsubmit = ev => { ev.preventDefault(); const v = ev.target.querySelector("input").value.trim(); send(v || "이 부분을 쉬운 말로 설명해 줘"); };
};

/* 기록: 원문 하이라이트 + 문단 아래 작은 상자 */
function placeNote(host, note, fresh = false) {
  const {str, pos} = textMap(host);
  const q = squash(note.quote), pre = squash(note.prefix || "");
  if (!q) return null;
  let at = pre ? str.indexOf(pre + q) : -1;
  at = at >= 0 ? at + pre.length : str.indexOf(q);
  if (at < 0) return null;  // 문서가 바뀌어 원문을 찾지 못함
  const seg = pos.slice(at, at + q.length);
  // 텍스트 노드마다 고른 구간을 <mark>로 감싼다 (뒤에서부터 해야 위치가 안 밀린다)
  const byNode = new Map();
  for (const [n, o] of seg) { const r = byNode.get(n) || [o, o]; r[0] = Math.min(r[0], o); r[1] = Math.max(r[1], o); byNode.set(n, r); }
  let last = null;
  for (const [n, [a, b]] of [...byNode].reverse()) {
    let mid = n;
    if (a > 0) mid = n.splitText(a);
    if (b - a + 1 < mid.nodeValue.length) mid.splitText(b - a + 1);
    const m = document.createElement("mark");
    m.className = "qa-mark"; m.dataset.note = note.id;
    mid.parentNode.insertBefore(m, mid); m.append(mid);
    last = last || m;
  }
  const box = h("div", "qa-note" + (fresh ? "" : " folded"));
  box.dataset.note = note.id;
  box.innerHTML = `<div class="qh"><span class="q">${esc(note.question)}</span><button class="qx" title="이 기록 지우기">지우기</button></div><div class="qa">${esc(note.answer)}</div>`;
  // 기록 상자는 고른 글이 있는 문단 바로 아래에 둔다
  const anchor = last, inHost = e => e && host.contains(e) && e !== host;
  const codeBlock = anchor.closest("pre");
  if (inHost(codeBlock)) { box.classList.add("in-code"); afterLine(codeBlock, anchor, box); return box; }
  const sum = anchor.closest("summary");                    // 접힌 상자(확인 문제 등)의 제목: 상자 바로 아래
  const li = anchor.closest("li");
  const cell = anchor.closest("td, th");
  const blk = anchor.closest("p, pre, h1, h2, h3, h4, figure, blockquote, .math[data-display], .ctitle");
  const cbody = anchor.closest(".cbody");
  if (inHost(sum)) sum.parentElement.after(box);
  else if (inHost(li)) li.append(box);
  else if (inHost(cell)) cell.closest("table").after(box);
  else if (inHost(blk)) blk.after(box);
  else if (inHost(cbody)) cbody.append(box);               // 문단 없이 글만 있는 상자 본문
  else {                                                   // 그 밖에는 문서 바로 밑 덩어리 다음
    let top = anchor;
    while (top.parentElement && top.parentElement !== host) top = top.parentElement;
    top.parentElement === host ? top.after(box) : host.append(box);
  }
  return box;
}
// 코드 블록에서 node가 있는 줄의 끝(줄바꿈 글자나 <br>) 바로 뒤에 box를 넣는다. 마지막 줄이면 블록 끝에
function afterLine(pre, node, box) {
  const w = document.createTreeWalker(pre, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {acceptNode: n =>
    n.nodeType === 1 && n.closest(".qa-note") || n.nodeType === 3 && n.parentElement.closest(".qa-note") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  w.currentNode = node;
  // node(표시한 <mark>) 안쪽은 건너뛰고 그 뒤부터 찾는다
  let n = node; while (n && !n.nextSibling && n !== pre) n = n.parentNode;
  if (!n || n === pre) { (pre.querySelector("code") || pre).append(box); return; }
  w.currentNode = n.nextSibling;
  for (let c = w.currentNode; c; c = w.nextNode()) {
    if (c.nodeType === 1 && c.tagName === "BR") { c.after(box); return; }
    if (c.nodeType === 3) {
      const i = c.nodeValue.indexOf("\n");
      if (i >= 0) { const rest = c.splitText(i + 1); rest.parentNode.insertBefore(box, rest); return; }
    }
  }
  (pre.querySelector("code") || pre).append(box);
}
async function applyNotes(host) {
  const doc = docKeyOf(host); if (!doc) return;
  $$(".qa-note", host).forEach(b => b.remove());
  $$("mark.qa-mark", host).forEach(m => m.replaceWith(...m.childNodes));
  host.normalize();
  for (const n of await API.doc_notes(doc)) placeNote(host, n);
}
document.addEventListener("click", async e => {
  const x = e.target.closest(".qa-note .qx");
  if (x) {
    const box = x.closest(".qa-note"), id = box.dataset.note, host = box.closest(".dpanel, #lDoc");
    if (!String(id).startsWith("tmp")) await API.delete_note(id);
    box.remove();
    $$(`mark.qa-mark[data-note="${id}"]`, host).forEach(m => m.replaceWith(...m.childNodes));
    host?.normalize();
    return;
  }
  const qh = e.target.closest(".qa-note .qh");
  if (qh) { qh.parentElement.classList.toggle("folded"); return; }
  const mk = e.target.closest("mark.qa-mark");
  if (mk) {
    const box = $(`.qa-note[data-note="${mk.dataset.note}"]`, mk.closest(".dpanel, #lDoc"));
    if (box) { box.classList.remove("folded"); box.scrollIntoView({block: "nearest", behavior: "smooth"}); box.classList.add("flash"); setTimeout(() => box.classList.remove("flash"), 900); }
  }
});
handlers.doc_stream = d => {
  const box = $(`.qa-note[data-rid="${d.id}"]`); if (!box) return;
  const qa = box.querySelector(".qa");
  if (qa.classList.contains("thinking")) { qa.classList.remove("thinking"); qa.textContent = ""; qa.classList.add("live"); }
  qa.textContent += d.text;
};
handlers.doc_answer = d => {
  const box = $(`.qa-note[data-rid="${d.id}"]`); if (!box) return;
  const qa = box.querySelector(".qa");
  qa.classList.remove("thinking", "live"); qa.textContent = d.message;
  if (d.note) {  // 기록 번호로 바꿔 단다 (지우기·다시 열기에 쓴다)
    const old = box.dataset.note;
    box.dataset.note = d.note;
    $$(`mark.qa-mark[data-note="${old}"]`).forEach(m => m.dataset.note = d.note);
  }
};


/* ---------------- 전체 검색 (⌘K) ---------------- */
const pal = $("#palette"), palIn = $("#palInput"), palRes = $("#palRes");
let palItems = [], palSel = 0, palTimer = null, palSeq = 0;
function openPalette() { pal.hidden = false; palIn.select(); palIn.focus(); if (!palIn.value) palRes.innerHTML = `<div class="palempty">문제, 개념, 개념 문서 본문, 문서에서 물은 질문과 답, 오답 기록을 한 번에 찾습니다. 낱말을 띄어 쓰면 모두 들어 있는 것만 찾습니다.</div>`; }
function closePalette() { pal.hidden = true; }
$$("[data-search]").forEach(b => b.onclick = openPalette);
pal.addEventListener("mousedown", e => { if (e.target === pal) closePalette(); });
document.addEventListener("keydown", e => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); pal.hidden ? openPalette() : closePalette(); }
}, true);
const hl = (text, terms) => {
  let out = esc(text);
  for (const t of terms) if (t) out = out.replace(new RegExp(t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi"), m => `<b class="hl">${m}</b>`);
  return out;
};
palIn.addEventListener("input", () => { clearTimeout(palTimer); palTimer = setTimeout(runSearch, 120); });
async function runSearch() {
  const q = palIn.value.trim(), seq = ++palSeq;
  if (!q) { palRes.innerHTML = ""; palItems = []; return; }
  const r = await API.search(q);
  if (seq !== palSeq) return;
  const terms = q.split(/\s+/);
  palItems = []; let html = "";
  const group = (name, rows, render) => {
    if (!rows?.length) return;
    html += `<div class="palgrp">${name}</div>`;
    for (const row of rows) { html += `<div class="palitem" role="option" data-i="${palItems.length}">${render(row)}</div>`; palItems.push(row); }
  };
  group("문제", r.problems?.map(x => ({...x, t: "problem"})), x => `<span class="tt">${hl(x.title, terms)}</span><span class="rt">Lv${x.level} · ${STATUS[x.status]}</span><span class="sn">${hl(x.sub || "", terms)}</span>`);
  group("개념", r.concepts?.map(x => ({...x, t: "concept"})), x => `<span class="tt">${hl(x.title, terms)}</span><span class="rt">개념 문서</span><span class="sn">${esc(x.sub)}</span>`);
  group("문서 내용", r.content?.map(x => ({...x, t: "content"})), x => `<span class="tt">${esc(x.title)}</span><span class="rt">${x.kind === "doc" ? "개념" : "문제문"} · ${x.count}곳</span><span class="sn">${hl(x.snippet, terms)}</span>`);
  group("내 질문", r.notes?.map(x => ({...x, t: "note"})), x => `<span class="tt">${hl(x.question, terms)}</span><span class="rt">${esc(x.title)}</span><span class="sn">${hl(x.snippet, terms)}</span>`);
  group("오답 기록", r.mistakes?.map(x => ({...x, t: "mistake"})), x => `<span class="tt">${hl(x.name, terms)}</span><span class="rt">${esc(x.title)} · ${esc(x.category)}</span>`);
  palRes.innerHTML = html || `<div class="palempty">“${esc(q)}”이(가) 들어 있는 곳이 없습니다.</div>`;
  palSel = 0; markSel();
}
function markSel() { $$(".palitem", palRes).forEach(el => el.setAttribute("aria-selected", +el.dataset.i === palSel)); $(`.palitem[data-i="${palSel}"]`, palRes)?.scrollIntoView({block: "nearest"}); }
palIn.addEventListener("keydown", e => {
  if (e.key === "Escape") { closePalette(); return; }
  if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); if (palItems.length) { palSel = (palSel + (e.key === "ArrowDown" ? 1 : -1) + palItems.length) % palItems.length; markSel(); } }
  if (e.key === "Enter" && palItems[palSel]) { e.preventDefault(); goResult(palItems[palSel]); }
});
palRes.addEventListener("click", e => { const it = e.target.closest(".palitem"); if (it) goResult(palItems[+it.dataset.i]); });
palRes.addEventListener("mousemove", e => { const it = e.target.closest(".palitem"); if (it && +it.dataset.i !== palSel) { palSel = +it.dataset.i; markSel(); } });

// 결과로 가기: 풀기 화면이면 개념은 문서 창 탭으로, 아니면 학습 화면으로 연다
const inSolve = () => !$("#solve").hidden;
async function showDoc(name) {
  if (inSolve()) { await openDoc(name); return $(`#dbody > .dpanel[data-tab="doc:${CSS.escape(name)}"]`); }
  await openConcept(name); return $("#lDoc");
}
async function goResult(x) {
  closePalette();
  const term = palIn.value.trim().split(/\s+/)[0];
  if (x.t === "problem" || x.t === "mistake") return openProblem(x.id || x.pid);
  if (x.t === "concept") return showDoc(x.name);
  if (x.t === "content") {
    if (x.kind === "pdoc") { await openProblem(x.key); return flashTerm($('#dbody > .dpanel[data-tab="problem"]'), term); }
    const host = await showDoc(x.key); setTimeout(() => flashTerm(host, term), 300); return;
  }
  if (x.t === "note") {
    let host;
    if (x.doc.startsWith("problem:")) { await openProblem(x.doc.split(":")[1]); host = $('#dbody > .dpanel[data-tab="problem"]'); }
    else if (x.doc.startsWith("code:")) {
      const rel = x.doc.slice(5); await openCode(rel);
      host = $("#solve").hidden ? $("#lDoc") : $(`#dbody > .dpanel[data-tab="${CSS.escape("code:" + rel)}"]`);
    }
    else host = await showDoc(x.doc);
    setTimeout(() => { const b = $(`.qa-note[data-note="${x.id}"]`, host); if (b) { b.classList.remove("folded"); b.scrollIntoView({block: "center"}); b.classList.add("flash"); setTimeout(() => b.classList.remove("flash"), 1200); } }, 500);
  }
}
// 문서 안에서 검색어가 처음 나오는 곳을 찾아 펼치고 잠깐 표시한다
function flashTerm(host, term) {
  if (!host || !term) return;
  const {str, pos} = textMap(host);
  const at = str.toLowerCase().indexOf(squash(term).toLowerCase());
  if (at < 0) return;
  const [n, o] = pos[at];
  let d = n.parentElement.closest("details");
  while (d) { d.open = true; d = d.parentElement.closest("details"); }
  const len = Math.min(squash(term).length, n.nodeValue.length - o);
  const mid = n.splitText(o); mid.splitText(len);
  const m = document.createElement("mark"); m.className = "search-hit"; mid.parentNode.insertBefore(m, mid); m.append(mid);
  m.scrollIntoView({block: "center"});
  setTimeout(() => { m.replaceWith(...m.childNodes); host.normalize(); }, 2500);
}


/* ---------------- 코치(AI) 준비 안내 ---------------- */
async function openSetup(force, tab) {
  const info = await API.setup_info();
  if (!force && info.server && info.model) return;
  try { if (!force && localStorage.getItem("kt-setup-later") === "1") return; } catch (_) {}
  S.setupTab = tab || S.setupTab || (info.provider && info.provider !== "ollama" ? "api" : "local");
  const seg = `<div class="seg plain big stabs" role="tablist">${[["local", "내 컴퓨터 (Ollama)"], ["api", "외부 API"]].map(([k, t]) =>
    `<button data-stab="${k}" aria-pressed="${S.setupTab === k}">${t}${(k === "api") === !!info.external ? " · 사용 중" : ""}</button>`).join("")}</div>`;
  if (S.setupTab === "api") await setupApi(info, seg); else setupLocal(info, seg);
  $("#setup").hidden = false;
  $$("#setupBody [data-stab]").forEach(b => b.onclick = () => openSetup(true, b.dataset.stab));
  $("#setupLater").onclick = () => { $("#setup").hidden = true; try { localStorage.setItem("kt-setup-later", "1"); } catch (_) {} };
}

function setupLocal(outer, seg) {
  // 외부 API를 쓰는 중이면 내 컴퓨터 Ollama의 상태(local)를 보여 준다
  const local = !outer.external, info = local ? outer : {...outer.local, recommend: outer.recommend, download: outer.download};
  const r = info.recommend, installed = info.installed || [];
  $("#setupBody").innerHTML = `
    <h2>코치(AI)를 준비해요</h2>${seg}
    <p>문제 풀기, 테스트, 반례 찾기는 지금도 쓸 수 있습니다. 코치의 말과 문서 질문에는 AI가 필요합니다. 내 컴퓨터에서 도는 AI(Ollama)를 쓰면 코드와 질문을 인터넷으로 보내지 않습니다.</p>
    <div class="steps">
      <div class="step ${info.server && local || installed.length ? "done" : ""}"><span class="n">${installed.length ? "✓" : "1"}</span><b>Ollama 설치</b>
        <span class="d">${installed.length || (info.server && local) ? "켜져 있습니다." : `<a href="${info.download}" target="_blank" rel="noopener">ollama.com/download</a>에서 받아 설치하고 실행해 주세요. 메뉴 막대에 라마 아이콘이 뜨면 됩니다.`}</span></div>
      <div class="step ${local && info.model ? "done" : ""}" id="stepModel"><span class="n">${local && info.model ? "✓" : "2"}</span><b>코치 모델 받기</b>
        <span class="d">${local && info.model ? `${esc(info.name)}이(가) 준비되어 있습니다.` : `이 컴퓨터 메모리 ${r.ram}GB → <code>${esc(r.model)}</code> (${r.size}) 를 추천합니다. 한 번만 받으면 됩니다.`}</span>
        <div class="bar" id="pullBar" hidden><i></i></div><span class="d" id="pullText"></span></div>
    </div>
    ${installed.length || (info.server && local) ? `<h3 class="ch">코치 모델</h3><div class="choices" id="modelChoices">
      ${[["auto", "자동 (추천)", "속도 우선(gemma4 e4b)을 씁니다"],
         ["accurate", "정확도 우선", "gemma4 12B · 7.2GB. 더 크고 느립니다. 메모리 16GB 이상에서 쓰세요"],
         ["fast", "속도 우선", "gemma4 e4b · 6.1GB. 응답이 약 2배 빠르고 메모리를 덜 씁니다"]].map(([k, t, d]) => {
        const need = k === "auto" ? r.choice : k, have = info.have?.[need];
        return `<button class="choice" data-choice="${k}" aria-pressed="${local && info.choice === k}"><b>${t}</b><span class="d">${esc(d)}</span>
          <span class="st">${have ? "받아 둠" : `받아야 함 · ${k === "fast" || (k === "auto" && r.choice === "fast") ? "6.1GB" : "7.2GB"}`}</span></button>`; }).join("")}
      <div class="choice custom ${local && info.choice === "custom" ? "on" : ""}"><b>다른 모델</b>
        <span class="d">Ollama에 있는 모델을 이름으로 고릅니다. 없으면 받습니다. 코치 말은 gemma4에 맞춰 다듬었으므로 다른 모델은 말투나 정확도가 다를 수 있습니다.</span>
        <div class="row"><input id="olName" list="olList" placeholder="예: qwen3:8b" value="${esc(info.choice === "custom" ? info.name : "")}" spellcheck="false" autocomplete="off">
        <datalist id="olList">${installed.map(n => `<option value="${esc(n)}">`).join("")}</datalist><button class="btn" id="olUse">이 모델 쓰기</button></div></div>
    </div>` : ""}
    <div class="acts">
      <button class="btn" id="setupLater">나중에</button>
      ${!installed.length && !(info.server && local) ? `<button class="btn" id="setupRetry">다시 확인</button>` : ""}
      ${local && info.server && !info.model ? `<button class="run" id="setupPull">모델 받기 (${r.size})</button>` : ""}
      ${local && info.server && info.model ? `<button class="run" id="setupOk">시작하기</button>` : ""}
    </div>`;
  $$("#modelChoices .choice[data-choice]").forEach(b => b.onclick = async () => {
    await API.set_coach_model(b.dataset.choice);
    const want = b.dataset.choice === "auto" ? r.choice : b.dataset.choice;
    if (!info.have?.[want]) {  // 아직 없으면 받기
      $("#pullBar").hidden = false; $("#pullText").textContent = "받기 시작";
      API.pull_model(want === "fast" ? "gemma4:e4b-it-qat" : "gemma4:12b-it-qat");
    }
    setAi(await API.ai_status());
    openSetup(true, "local");
  });
  $("#olUse") && ($("#olUse").onclick = async () => {
    const name = $("#olName").value.trim(); if (!name) { $("#olName").focus(); return; }
    const res = await API.set_ollama_model(name);
    if (res.pulling) { $("#pullBar").hidden = false; $("#pullText").textContent = `${res.name} 받기 시작`; return; }
    setAi(res); openSetup(true, "local");
  });
  $("#setupRetry") && ($("#setupRetry").onclick = () => openSetup(true, "local"));
  $("#setupOk") && ($("#setupOk").onclick = () => { $("#setup").hidden = true; });
  $("#setupPull") && ($("#setupPull").onclick = e => {
    e.target.disabled = true; e.target.innerHTML = waiting("받고 있습니다");
    $("#pullBar").hidden = false; API.pull_model(r.model);
  });
}

async function setupApi(info, seg) {
  const cfg = await API.api_settings();
  let cur = S.apiPick || (cfg.provider !== "ollama" ? cfg.provider : "openai");
  const draw = () => {
    const p = cfg.providers[cur], using = info.external && cfg.provider === cur;
    $("#setupBody").innerHTML = `
      <h2>코치(AI)를 준비해요</h2>${seg}
      <p>내 컴퓨터가 AI를 돌리기 버거우면 외부 회사의 AI를 쓸 수 있습니다. 내 API 키로 요청하므로 요금은 그 회사 계정에 나옵니다.</p>
      <p class="warnline">외부 API를 쓰면 지금 푸는 문제, 내 코드, 테스트 결과, 질문이 그 회사 서버로 보내집니다.</p>
      <div class="provs">${Object.entries(cfg.providers).map(([k, v]) =>
        `<button data-prov="${k}" aria-pressed="${k === cur}">${esc(v.label)}${info.external && cfg.provider === k ? " ✓" : ""}</button>`).join("")}</div>
      <div class="form">
        <label>주소 <input id="apBase" value="${esc(p.base)}" placeholder="${cur === "custom" ? "예: http://127.0.0.1:1234/v1" : esc(p.default_base)}" spellcheck="false" autocomplete="off"></label>
        <label>API 키 <input id="apKey" type="password" value="${esc(p.key)}" placeholder="${cur === "custom" ? "필요 없으면 비워 둡니다" : "붙여 넣기"}" spellcheck="false" autocomplete="off">
          ${p.key_url ? `<a class="d" href="${p.key_url}" target="_blank" rel="noopener">키 받는 곳</a>` : ""}</label>
        <label>모델 <span class="row"><input id="apModel" list="apList" value="${esc(p.model)}" placeholder="이름을 쓰거나 목록에서 고릅니다" spellcheck="false" autocomplete="off">
          <datalist id="apList"></datalist><button class="btn" id="apList2">목록 불러오기</button></span></label>
        <p class="d">키는 이 컴퓨터의 앱 설정 파일에만 저장되고, 화면에는 끝 네 글자만 보입니다. 생각(추론)하는 모델은 느리므로 빠르고 작은 모델을 추천합니다.</p>
        <p class="d" id="apMsg" role="status"></p>
      </div>
      <div class="acts">
        <button class="btn" id="setupLater">나중에</button>
        ${info.external ? `<button class="btn" id="apLocal">내 컴퓨터로 돌아가기</button>` : ""}
        <button class="btn" id="apTest">연결 확인</button>
        <button class="run" id="apSave">${using ? "저장" : "저장하고 이 API 쓰기"}</button>
      </div>`;
    $$("#setupBody [data-stab]").forEach(b => b.onclick = () => openSetup(true, b.dataset.stab));
    $("#setupLater").onclick = () => { $("#setup").hidden = true; try { localStorage.setItem("kt-setup-later", "1"); } catch (_) {} };
    $$(".provs button").forEach(b => b.onclick = () => { cur = S.apiPick = b.dataset.prov; draw(); });
    const vals = () => [cur, $("#apBase").value, $("#apKey").value, $("#apModel").value];
    const msg = (t, bad) => { const m = $("#apMsg"); m.innerHTML = t; m.className = "d" + (bad ? " bad" : " good"); };
    $("#apList2").onclick = async e => {
      e.target.disabled = true; msg(waiting("모델 목록을 받고 있습니다"));
      const r = await API.api_models(...vals().slice(0, 3));
      e.target.disabled = false;
      if (!r.ok) return msg(esc(r.error), true);
      $("#apList").innerHTML = r.models.map(m => `<option value="${esc(m)}">`).join("");
      msg(`모델 ${r.models.length}개를 찾았습니다. 모델 칸을 눌러 고르세요.`);
      $("#apModel").focus();
    };
    $("#apTest").onclick = async e => {
      if (!$("#apModel").value.trim()) { msg("모델 이름을 먼저 정해 주세요.", true); return $("#apModel").focus(); }
      e.target.disabled = true; msg(waiting("짧은 질문을 보내 보고 있습니다"));
      const r = await API.api_test(...vals());
      e.target.disabled = false;
      r.ok ? msg(`연결되었습니다. “${esc(r.text)}” · ${r.sec}초`) : msg(esc(r.error), true);
    };
    $("#apSave").onclick = async () => {
      if (!$("#apModel").value.trim()) { msg("모델 이름을 먼저 정해 주세요.", true); return $("#apModel").focus(); }
      if (cur === "custom" && !$("#apBase").value.trim()) { msg("서버 주소를 넣어 주세요.", true); return $("#apBase").focus(); }
      if (cur !== "custom" && !$("#apKey").value.trim()) { msg("API 키를 넣어 주세요.", true); return $("#apKey").focus(); }
      const st = await API.save_api(...vals());
      setAi(st);
      await openSetup(true, "api");
      const m = $("#apMsg"); m.textContent = "저장했습니다. 이제 코치가 이 API를 씁니다."; m.className = "d good";
    };
    $("#apLocal") && ($("#apLocal").onclick = async () => { setAi(await API.use_local()); openSetup(true, "local"); });
  };
  draw();
}
const fmtGB = b => (b / 2 ** 30).toFixed(1);
handlers.pull = d => {
  if (!$("#pullBar")) return;
  if (d.total) $("#pullBar i").style.width = `${Math.round(d.done / d.total * 100)}%`;
  $("#pullText").textContent = d.total ? `${fmtGB(d.done)} / ${fmtGB(d.total)} GB · ${d.status}` : d.status;
};
handlers.model_ready = st => setAi(st);
handlers.pull_done = d => {
  if (d.ok) { setAi(d.status); openSetup(true); }
  else if ($("#pullText")) { $("#pullText").textContent = `받지 못했습니다: ${d.error}`; const b = $("#setupPull"); if (b) { b.disabled = false; b.textContent = "다시 받기"; } }
};
$$(".aistat").forEach(el => el.addEventListener("click", () => openSetup(true)));


/* ---------------- 정보 창 ---------------- */
const BLOG_ABOUT = "https://hong-iron.github.io/Hongs_Blog/about/";
async function openAbout() {
  const a = await API.about();
  $("#aboutBody").innerHTML = `
    <button class="x close" id="aboutClose" aria-label="닫기">×</button>
    <div class="ahead"><img src="icon.svg" alt="" class="alogo"><div><h2>KOTEacher</h2>
      <p class="asub">KOTE(코테) + Teacher · 버전 ${esc(a.version)}</p></div></div>
    <p>내 컴퓨터에서 도는 AI 코치와 함께 푸는 코딩 테스트 연습 프로그램입니다. 판정은 테스트가 하고, 코치는 정답 대신 질문으로 스스로 찾게 돕습니다.</p>
    <dl class="facts">
      <dt>들어 있는 것</dt><dd>프로그래머스 ${a.problems}문제 · 알고리즘 개념 문서 ${a.concepts}개</dd>
      <dt>코치</dt><dd>${a.coach ? esc(a.coach) : "아직 준비되지 않았습니다"}</dd>
      <dt>내 기록</dt><dd><code>${esc(a.data)}</code></dd>
      <dt>이 컴퓨터</dt><dd>${esc(a.os)} · Python ${esc(a.python)}</dd>
    </dl>
    <div class="arow"><button class="btn" id="aboutUpd">새 버전 확인</button><span class="d" id="aboutUpdMsg"></span></div>
    <p class="fine">문제의 저작권은 프로그래머스와 출제처에 있습니다. 편집기 Monaco, 수식 KaTeX, 그림 Mermaid, 창 pywebview, 코치 Ollama·gemma4를 씁니다. 프로그램은 MIT 라이선스로 공개되어 있습니다.</p>
    <div class="afoot"><a href="${esc(a.repo)}" target="_blank" rel="noopener">GitHub</a><a href="${esc(a.repo)}/releases" target="_blank" rel="noopener">릴리스</a>
      <span class="sp"></span><span class="made">made by <a href="${BLOG_ABOUT}" target="_blank" rel="noopener">Hong-Iron</a></span></div>`;
  $("#about").hidden = false;
  $("#aboutClose").onclick = closeAbout;
  $("#aboutUpd").onclick = async e => {
    const m = $("#aboutUpdMsg"); e.target.disabled = true; m.innerHTML = waiting("확인하고 있습니다");
    const r = await API.check_update(); e.target.disabled = false;
    m.innerHTML = !r.ok ? `확인하지 못했습니다 (${esc(r.error)})`
      : r.newer ? `새 버전 ${esc(r.latest)}이 있습니다. <a href="${esc(r.url)}" target="_blank" rel="noopener">받으러 가기</a>` : "최신 버전을 쓰고 있습니다.";
  };
}
const closeAbout = () => { $("#about").hidden = true; };
$("#openAbout").onclick = openAbout;
$("#about").addEventListener("click", e => { if (e.target.id === "about") closeAbout(); });  // 바깥을 누르면 닫는다
document.addEventListener("keydown", e => { if (e.key === "Escape" && !$("#about").hidden) closeAbout(); });

/* ---------------- 풀이 기록 ---------------- */
const RES = {solved: "통과", exam: "실전 통과", helped: "힌트로 통과", viewed: "풀이 봄", open: "미완"};
const fmtWhen = t => { const d = new Date(t * 1000); return `${d.getMonth() + 1}월 ${d.getDate()}일 ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`; };
const fmtDay = t => { const d = new Date(t * 1000); return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일`; };
let histAll = [], histF = "";
async function openHistory() {
  histAll = await API.history(null);
  drawHistory(); show("history");
}
function drawHistory() {
  const rows = histAll.filter(r => !histF || r.res === histF);
  let html = "", day = "";
  for (const r of rows) {
    const d = fmtDay(r.last_t);
    if (d !== day) { html += `<div class="hday">${d}</div>`; day = d; }
    html += `<div class="hrow" data-aid="${r.id}" tabindex="0"><span class="ti">${esc(r.title)} <span class="note">Lv${r.level ?? "?"}</span></span><span class="pill ${r.res}">${RES[r.res]}</span>
      <span class="sub">${fmtWhen(r.last_t).split(" ").slice(2).join(" ")} · ${r.minutes}분 · 실행 ${r.runs}번 · 힌트 ${r.hints_opened || 0}개${r.mistakes ? ` · 오답 ${r.mistakes}` : ""}${r.coach ? ` · 코치 ${r.coach}번` : ""}</span></div>`;
  }
  $("#hList").innerHTML = html || `<p class="note" style="padding:14px">아직 기록이 없습니다. 문제를 열고 한 번이라도 실행하면 여기에 남습니다.</p>`;
}
$$("#histSeg button").forEach(b => b.onclick = () => { histF = b.dataset.f; $$("#histSeg button").forEach(x => x.setAttribute("aria-pressed", x === b)); drawHistory(); });
$("#hList").addEventListener("click", e => { const r = e.target.closest(".hrow"); if (r) showAttempt(+r.dataset.aid); });
$("#hList").addEventListener("keydown", e => { const r = e.target.closest(".hrow"); if (r && e.key === "Enter") showAttempt(+r.dataset.aid); });
const codeHtml = code => `<pre class="hcode">${(code || "").split("\n").map(l => `<span>${esc(l) || " "}</span>`).join("")}</pre>`;
const snapExam = s => s.exam === "timeup" ? "제한 시간이 끝난 뒤 계속 풂" : s.exam === "submit" ? (s.submit ? `실전 제출 · 숨은 검사 ${s.submit.total}개 중 ${s.submit.passed}개` : "실전 제출 · 실행 실패") : "실전 예시 실행";
async function showAttempt(aid) {
  $$(".hrow").forEach(r => r.setAttribute("aria-selected", +r.dataset.aid === aid));
  const meta = histAll.find(r => r.id === aid), d = await API.attempt(aid);
  const snaps = d.snapshots, last = snaps.at(-1);
  let shown = last;
  const box = $("#hDetail");
  const draw = () => {
    box.innerHTML = `<h1>${esc(meta.title)} <span class="pill ${meta.res}">${RES[meta.res]}</span></h1>
      <p class="note">${fmtWhen(meta.started)} 시작 · ${meta.minutes}분 · 실행 ${meta.runs}번 · 힌트 ${meta.hints_opened || 0}개</p>
      <div class="acts"><button class="btn" data-h="open">이 문제 열기</button><button class="run" data-h="code">이 코드로 다시 열기</button></div>
      <h2>코드 (${shown === last ? "마지막 실행" : fmtWhen(shown.t).split(" ").slice(2).join(" ") + " 실행"})</h2>${codeHtml(shown?.code)}
      <h2>실행 흐름 · 누르면 그때 코드를 봅니다</h2><ul class="tl">${snaps.map(s => `<li class="pick" data-sid="${s.id}"><span class="tm">${fmtWhen(s.t).split(" ").slice(2).join(" ")}</span>
        <span class="${s.passed ? "ok" : "bad"}">${s.passed ? "✓" : "✗"}</span><span class="tx">${s.reset ? "처음부터 다시 풀기 전에 저장한 코드" : s.exam ? snapExam(s) : s.passed ? "모두 통과" : esc(evidence(s.fact) || s.fact.msg || "실패")}</span></li>`).join("")}</ul>
      ${d.coach.length ? `<h2>코치가 한 말</h2><ul class="log">${d.coach.map(c => `<li><span class="tm">${fmtWhen(c.t).split(" ").slice(2).join(" ")}</span><span>${esc(c.message)}</span><span></span></li>`).join("")}</ul>` : ""}
      ${d.mistakes.length ? `<h2>오답 기록</h2>${d.mistakes.map(m => mistakeRow({...m, title: meta.title})).join("")}` : ""}`;
  };
  draw();
  box.onclick = e => {
    const li = e.target.closest("li.pick");
    if (li) { shown = snaps.find(s => s.id === +li.dataset.sid); draw(); return; }
    const b = e.target.closest("[data-h]");
    if (b?.dataset.h === "open") openProblem(meta.problem_id);
    if (b?.dataset.h === "code") openProblem(meta.problem_id, null, shown.code);
  };
  $(".hist").classList.add("detail");
}
$("#openHist").onclick = openHistory;
$("#histBack").onclick = () => { $(".hist").classList.remove("detail"); show("home"); };

// 풀기 화면의 '풀이 기록' 탭: 이 문제의 지난 코드 불러오기 (되돌리기 ⌘Z 가능)
async function loadProblemHistory() {
  if (!S.p) return;
  // 지금 시도와, 빈 틀 그대로 끝난 시도는 빼고 보여 준다
  const blank = (S.p.template || "").trim();
  const rows = (await API.history(S.p.id)).filter(r => r.id !== S.p.aid && (r.last_code || "").trim() && (r.last_code || "").trim() !== blank).slice(0, 20);
  const preview = code => {
    const ls = (code || "").split("\n"), body = ls.filter(l => l.trim() && !/^\s*(def solution|import |from |#)/.test(l));
    return `${ls.filter(l => l.trim()).length}줄 · ${esc((body[0] || ls[0] || "").trim().slice(0, 60))}`;
  };
  $("#histPanel").innerHTML = rows.length ? `<ul class="phist">${rows.map(r => `<li>
      <span class="when">${fmtWhen(r.last_t)}</span>
      <span class="pill ${r.res}">${RES[r.res]}</span>
      <span class="meta">${r.was_reset ? "처음부터 전에 저장 · " : ""}${r.minutes}분 · 실행 ${r.runs}번 · 힌트 ${r.hints_opened || 0}개<code>${preview(r.last_code)}</code></span>
      <button class="chip" data-load="${r.id}">이 코드 불러오기</button></li>`).join("")}</ul>`
    : `<p class="note" style="margin:4px 0">이 문제의 지난 기록이 없습니다.</p>`;
}
$("#histPanel").addEventListener("click", async e => {
  const b = e.target.closest("[data-load]"); if (!b) return;
  const d = await API.attempt(+b.dataset.load), code = d.snapshots.at(-1)?.code;
  if (!code) return;
  const model = S.editor.getModel();
  S.editor.executeEdits("history", [{range: model.getFullModelRange(), text: code}]);  // ⌘Z로 되돌릴 수 있게
  addLog("sys", "기록", "지난 코드를 불러왔습니다. ⌘Z로 되돌릴 수 있습니다.");
});


/* ---------------- 개념 코드 보기 ---------------- */
const ROLE = {verify: "검증", impl: "구현", bench: "실험", plot: "그림 만들기", fig1: "그림", fig2: "그림", fig3: "그림"};
async function openCode(rel) {
  // 풀기 화면이면 문서 창의 탭으로, 홈·학습 화면이면 학습 화면에 펼친다
  const d = await API.code_file(rel);
  const html = await codePanelHtml(d);
  if (!$("#solve").hidden) {
    const key = "code:" + rel;
    if (!S.tabs.find(t => t.key === key)) {
      S.tabs.push({key, title: d.name.replace(/^\d+_/, ""), num: ROLE[d.role] || d.kind});
      const panel = h("div", "dpanel doc codeview"); panel.dataset.tab = key; panel.dataset.doc = "code:" + rel; panel.hidden = true; panel.innerHTML = html;
      $("#dbody").append(panel);
      applyNotes(panel);
    }
    setPanes(true, S.rightOn ?? true); activateTab(key);
    return;
  }
  // 홈·학습 화면: 학습 화면에 코드만 펼친다
  $("#lTitle").textContent = d.name; $("#lAlias").textContent = ROLE[d.role] || d.kind; $("#lAlias").hidden = false;
  $("#lDoc").innerHTML = html; $("#lDoc").dataset.doc = "code:" + rel; $("#lDoc").scrollTop = 0;
  $("#lProblems").innerHTML = `<p class="note">개념 문서의 '개념 코드'에서 열었습니다. 코드를 드래그하면 그 부분을 코치에게 물을 수 있습니다.</p>`;
  show("learn");
  applyNotes($("#lDoc"));
}
async function codePanelHtml(d) {
  if (d.kind === "svg") return `<h1>${esc(d.name)}</h1><figure class="fig">${d.text.replace(/^<\?xml[^>]*>\s*/, "")}</figure>`;
  await loadMonaco();
  const colored = await monaco.editor.colorize(d.text, "python", {tabSize: 4});
  const needs = d.needs.length ? `<p class="note">이 코드는 ${d.needs.join(", ")}가 있어야 실행됩니다. 그림은 이미 개념 문서 안에 들어 있습니다.</p>` : "";
  return `<h1>${esc(d.name)}</h1>
    <p class="note">${{verify: "개념 문서의 주장이 맞는지 확인하는 코드입니다.", impl: "개념을 직접 구현하고 스스로 시험하는 코드입니다.", bench: "입력 크기에 따라 걸리는 시간을 재는 실험 코드입니다.", plot: "문서의 그림을 만드는 코드입니다."}[d.role] || ""}</p>
    ${needs}<div class="acts"><button class="run" data-runcode="${esc(d.path)}">실행해 보기</button><button class="btn" data-copycode>코드 복사</button></div>
    <pre class="code colored"><code>${colored}</code></pre><pre class="runout" hidden></pre>`;
}
document.addEventListener("click", async e => {
  const run = e.target.closest("[data-runcode]");
  if (run) {
    const box = run.closest(".codeview, #lDoc").querySelector(".runout");
    box.hidden = false; box.className = "runout"; box.innerHTML = waiting("실행하고 있습니다");
    const r = await API.run_code(run.dataset.runcode);
    box.classList.add(r.ok ? "ok" : "bad"); box.textContent = `${r.ok ? "✓" : "✗"} ${r.sec}초\n${r.out}`;
    return;
  }
  const cp = e.target.closest("[data-copycode]");
  if (cp) {
    const code = codeText(cp.closest(".codeview, #lDoc").querySelector("pre.colored"));
    try { await navigator.clipboard.writeText(code); cp.textContent = "복사했습니다"; } catch (_) { cp.textContent = "복사하지 못했습니다"; }
    setTimeout(() => cp.textContent = "코드 복사", 1500);
  }
});

/* ---------------- 시작 ---------------- */
// 맥이 아니면 단축키 표시를 Ctrl로 바꾼다 (동작은 Monaco·키 처리기가 이미 Ctrl을 받는다)
if (!/Mac|iPhone|iPad/.test(navigator.platform)) {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = walker.nextNode());) if (n.nodeValue.includes("⌘")) n.nodeValue = n.nodeValue.replace(/⌘⇧/g, "Ctrl+Shift+").replace(/⌘/g, "Ctrl+").replace(/Ctrl\+↵/g, "Ctrl+Enter");
  $$("[title]").forEach(el => { el.title = el.title.replace(/⌘⇧/g, "Ctrl+Shift+").replace(/⌘/g, "Ctrl+"); });
}
function start() {
  boot().then(() => { API.log(`boot ok · 문제 ${S.problems.length}개`); openSetup(false); }).catch(e => API.log("boot 실패 " + e));
  loadMonaco().then(() => API.log("monaco ok")).catch(e => API.log("monaco 실패 " + e));
  window.addEventListener("error", e => API.log(`JS 오류 ${e.message} @${e.lineno}`));
}
if (window.pywebview?.api) { API = window.pywebview.api; start(); }
else {
  window.addEventListener("pywebviewready", () => { API = window.pywebview.api; start(); });
  setTimeout(() => { if (!API && location.protocol.startsWith("http")) { API = devBridge(); start(); } }, 400);
}
