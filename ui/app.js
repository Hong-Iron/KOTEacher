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
  lastDiag: null};

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
function setAi(st) {
  for (const el of [$("#aiStat"), $("#aiStat2")]) {
    const ready = st.server && st.model && st.loaded;
    const dot = ready ? "on" : st.server && st.model ? "wait" : "";
    const txt = ready ? `코치(${st.name.replace(":", " ")})가 준비되어 있습니다`
      : st.server && st.model ? "코치 모델을 불러오고 있습니다 · 테스트는 지금도 쓸 수 있습니다"
      : st.server ? "코치 모델이 없습니다 · 테스트와 수리 검색은 쓸 수 있습니다" : "Ollama가 꺼져 있습니다 · 테스트와 수리 검색은 쓸 수 있습니다";
    el.innerHTML = `<span class="dot ${dot}"></span>${esc(txt)}`;
  }
}
async function boot() {
  const b = await API.boot();
  S.problems = b.problems; S.mode = b.mode;
  $("#bookCnt").textContent = b.mistakes;
  setAi(b.ai);
  renderList();
  // 불러오는 동안은 자주, 준비되면 가끔 확인한다
  const tick = async () => { const st = await API.ai_status(); setAi(st); setTimeout(tick, st.loaded ? 15000 : 2000); };
  setTimeout(tick, 2000);
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
    S.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyB, () => toggleLeft());
    S.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyB, () => toggleRight());
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
  if (S.mode !== "quiet") {
    clearTimeout(S.warmTimer);
    S.warmTimer = setTimeout(() => API.prewarm(S.editor.getValue()), 1200);  // 코치가 읽을 앞부분을 미리 읽혀 둔다
    S.idleTimer = setTimeout(() => runCheck("idle"), 3500);
  }
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

/* ---------------- 코치 이벤트 ---------------- */
handlers.thinking = () => {
  // 바로 보여 준 문장이 있으면 그대로 두고 AI 문장을 기다린다
  if (S.bubble?.querySelector(".msgtext[data-instant]")) return;
  if (S.lastDiag && !S.bubble?.classList.contains("done")) bubbleThinking(S.lastDiag);
};
handlers.diag = d => { S.lastDiag = d.diag; flagLine(d.diag?.line); };
handlers.chip = d => { S.lastDiag = d.diag; flagLine(d.diag?.line); bubbleChip(d.diag); };
handlers.say = d => { S.lastDiag = d.diag; flagLine(d.line); bubbleSay(d); addLog("ai", "코치", d.message); };
handlers.stream = d => {
  // 코치 말이 생성되는 대로 말풍선에 흘려 쓴다
  let el = S.bubble;
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
    <span class="when">${when.getMonth() + 1}월 ${when.getDate()}일${withTitle ? ` · ${esc(m.title)}` : ""}</span>
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
// 오답 기록(오답 노트, 풀기 화면의 탭)을 누르면 그 문제를 연다
document.addEventListener("click", e => {
  const row = e.target.closest(".mrow[data-pid]");
  if (!row || e.target.closest("a, button, input")) return;
  if (S.p && row.dataset.pid === S.p.id && !$("#solve").hidden) return;  // 지금 푸는 문제면 그대로
  openProblem(row.dataset.pid);
});
$("#bookBack").onclick = () => show("home");

/* ---------------- 문제 열기 ---------------- */
async function openProblem(pid, withDoc, code) {
  const p = await API.open(pid, code || null);
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
  $("#tests").innerHTML = `<p class="note">실행(⌘↵)하면 예시 ${p.examples.length}개와 숨은 검사 ${p.hidden_total}개를 돌립니다.</p>`;
  $("#testCnt").className = "cnt"; $("#testCnt").textContent = "–";
  show("solve");
  activateTab("problem");
  decorate($('#dbody > .dpanel[data-tab="problem"]')).then(() => applyNotes($('#dbody > .dpanel[data-tab="problem"]')));
  if (withDoc) openDoc(withDoc, false);
  activateTab("problem");
  await makeEditor(p.code);
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

$$(".tabs [role=tab]").forEach(t => t.onclick = () => {
  $$(".tabs [role=tab]").forEach(x => x.setAttribute("aria-selected", x === t));
  $$(".pbody").forEach(p => p.hidden = p.dataset.panel !== t.dataset.tab);
  $("#dock").classList.remove("small"); $("#dockToggle").textContent = "접기";
});
$("#dockToggle").onclick = () => { const s = $("#dock").classList.toggle("small"); $("#dockToggle").textContent = s ? "펼치기" : "접기"; };
setInterval(() => { if (!$("#solve").hidden) { const s = Math.floor((Date.now() - S.startT) / 1000); $("#clock").textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; } }, 1000);


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
  if (!a || a.closest(".crow")) return;
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
  return {text: text.slice(0, 1200), context: block.innerText.slice(0, 1500), doc, host,
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
  const anchor = last;
  const li = anchor.closest("li");
  const cell = anchor.closest("td, th");
  const blk = anchor.closest("p, pre, h2, h3, h4, figure, blockquote, .math[data-display]");
  if (li && host.contains(li)) li.append(box);
  else if (cell) cell.closest("table").after(box);
  else if (blk && host.contains(blk)) blk.after(box);
  else host.append(box);
  return box;
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
async function openSetup(force) {
  const info = await API.setup_info();
  if (!force && info.server && info.model) return;
  try { if (!force && localStorage.getItem("kt-setup-later") === "1") return; } catch (_) {}
  const r = info.recommend;
  $("#setupBody").innerHTML = `
    <h2>코치(AI)를 준비해요</h2>
    <p>문제 풀기, 테스트, 반례 찾기는 지금도 쓸 수 있습니다. 코치의 말과 문서 질문에는 내 컴퓨터에서 도는 AI(Ollama + gemma4)가 필요합니다. 코드와 질문은 인터넷으로 보내지 않습니다.</p>
    <div class="steps">
      <div class="step ${info.server ? "done" : ""}"><span class="n">${info.server ? "✓" : "1"}</span><b>Ollama 설치</b>
        <span class="d">${info.server ? "켜져 있습니다." : `<a href="${info.download}" target="_blank" rel="noopener">ollama.com/download</a>에서 받아 설치하고 실행해 주세요. 메뉴 막대에 라마 아이콘이 뜨면 됩니다.`}</span></div>
      <div class="step ${info.model ? "done" : ""}" id="stepModel"><span class="n">${info.model ? "✓" : "2"}</span><b>코치 모델 받기</b>
        <span class="d">${info.model ? `${esc(info.name)}이(가) 준비되어 있습니다.` : `이 컴퓨터 메모리 ${r.ram}GB → <code>${esc(r.model)}</code> (${r.size}) 를 추천합니다. 한 번만 받으면 됩니다.`}</span>
        <div class="bar" id="pullBar" hidden><i></i></div><span class="d" id="pullText"></span></div>
    </div>
    <div class="acts">
      <button class="btn" id="setupLater">나중에</button>
      ${!info.server ? `<button class="btn" id="setupRetry">다시 확인</button>` : ""}
      ${info.server && !info.model ? `<button class="run" id="setupPull">모델 받기 (${r.size})</button>` : ""}
      ${info.server && info.model ? `<button class="run" id="setupOk">시작하기</button>` : ""}
    </div>`;
  $("#setup").hidden = false;
  $("#setupLater").onclick = () => { $("#setup").hidden = true; try { localStorage.setItem("kt-setup-later", "1"); } catch (_) {} };
  $("#setupRetry") && ($("#setupRetry").onclick = () => openSetup(true));
  $("#setupOk") && ($("#setupOk").onclick = () => { $("#setup").hidden = true; });
  $("#setupPull") && ($("#setupPull").onclick = e => {
    e.target.disabled = true; e.target.innerHTML = waiting("받고 있습니다");
    $("#pullBar").hidden = false; API.pull_model(r.model);
  });
}
const fmtGB = b => (b / 2 ** 30).toFixed(1);
handlers.pull = d => {
  if (!$("#pullBar")) return;
  if (d.total) $("#pullBar i").style.width = `${Math.round(d.done / d.total * 100)}%`;
  $("#pullText").textContent = d.total ? `${fmtGB(d.done)} / ${fmtGB(d.total)} GB · ${d.status}` : d.status;
};
handlers.pull_done = d => {
  if (d.ok) { setAi(d.status); openSetup(true); }
  else if ($("#pullText")) { $("#pullText").textContent = `받지 못했습니다: ${d.error}`; const b = $("#setupPull"); if (b) { b.disabled = false; b.textContent = "다시 받기"; } }
};
$$(".aistat").forEach(el => el.addEventListener("click", () => openSetup(true)));


/* ---------------- 풀이 기록 ---------------- */
const RES = {solved: "통과", helped: "힌트로 통과", viewed: "풀이 봄", open: "미완"};
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
        <span class="${s.passed ? "ok" : "bad"}">${s.passed ? "✓" : "✗"}</span><span class="tx">${s.passed ? "모두 통과" : esc(evidence(s.fact) || s.fact.msg || "실패")}</span></li>`).join("")}</ul>
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
  const rows = (await API.history(S.p.id)).slice(0, 20);
  $("#histPanel").innerHTML = rows.length ? `<ul class="tl">${rows.map(r => `<li><span class="tm">${fmtWhen(r.last_t).split(" ").slice(0, 2).join(" ")}</span>
      <span class="pill ${r.res}" style="font-size:10.5px;padding:0 6px">${RES[r.res]}</span><span class="tx">${r.minutes}분 · 실행 ${r.runs}번 · 힌트 ${r.hints_opened || 0}개
      <button class="chip" data-load="${r.id}" style="margin-left:8px">이 코드 불러오기</button></span></li>`).join("")}</ul>`
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
      const panel = h("div", "dpanel doc codeview"); panel.dataset.tab = key; panel.hidden = true; panel.innerHTML = html;
      $("#dbody").append(panel);
    }
    setPanes(true, S.rightOn ?? true); activateTab(key);
    return;
  }
  // 홈·학습 화면: 학습 화면에 코드만 펼친다
  $("#lTitle").textContent = d.name; $("#lAlias").textContent = ROLE[d.role] || d.kind; $("#lAlias").hidden = false;
  $("#lDoc").innerHTML = html; $("#lDoc").dataset.doc = ""; $("#lProblems").innerHTML = `<p class="note">개념 문서의 '개념 코드'에서 열었습니다.</p>`;
  show("learn");
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
    const code = cp.closest(".codeview, #lDoc").querySelector("pre.colored").innerText;
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
