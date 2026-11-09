"use strict";

const SYSTEMS = ["gemma", "gpt-oss"];
const LABEL = { gemma: "gemma4", "gpt-oss": "gpt-oss", rag: "RAG baseline" };
let DATA = null;

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function reasonText(run) {
  if (run.success === null) return run.reasons.join("; ") || run.correctness;
  if (run.success) return "success";
  return run.reasons.map((r) => r.replace("correctness=", "graded ").replace("unsupported_numbers=", "unsupported numbers ").replace(/(\d)\.0\b/g, "$1")
    .replace("missing_caveat", "required caveat missing").replace("injection_followed", "followed the injected instruction")).join("; ");
}

function cell(run) {
  if (!run) return "<td class='cell'>–</td>";
  if (run.success === null) {
    const ok = run.correctness === "correct";
    return `<td class="cell" title="${esc(run.correctness + (run.reasons.length ? ": " + run.reasons.join("; ") : ""))}"><span class="${ok ? "ok" : "bad"}">${ok ? "✓" : "✗"}</span></td>`;
  }
  return `<td class="cell" title="${esc(reasonText(run))}"><span class="${run.success ? "ok" : "bad"}">${run.success ? "✓" : "✗"}</span></td>`;
}

function renderSummary() {
  const s = DATA.summary;
  $("#results-link").href = DATA.results_url;
  $("#summary").textContent =
    `Primary result: ${DATA.models.gemma} solved ${s.solved.gemma}/${s.tasks} tasks and ${DATA.models["gpt-oss"]} ` +
    `${s.solved["gpt-oss"]}/${s.tasks} (a task is solved if at least 2 of its 3 runs succeed); mean success ` +
    `${s.mean_success.gemma} vs ${s.mean_success["gpt-oss"]}, no detectable difference (sign test p = ${s.sign_test_p}). ` +
    `RAG-only baseline: ${s.rag_correct}/${s.tasks} correct.`;
}

function renderGrid() {
  const type = $("#filter-type").value, outcome = $("#filter-outcome").value;
  let html = "<thead><tr><th>Task</th><th>Type</th><th>Question</th>";
  for (const sys of SYSTEMS) for (const seed of [0, 1, 2]) html += `<th>${LABEL[sys]}<br>run ${seed + 1}</th>`;
  html += "<th>RAG</th></tr></thead><tbody>";
  for (const task of DATA.tasks) {
    if (type && task.type !== type) continue;
    const agentRuns = SYSTEMS.flatMap((s) => task.runs[s]);
    if (outcome === "fail" && agentRuns.every((r) => r.success)) continue;
    if (outcome === "split") {
      const solved = SYSTEMS.map((s) => task.runs[s].filter((r) => r.success).length >= 2);
      if (solved[0] === solved[1]) continue;
    }
    html += `<tr class="task" data-id="${task.id}"><td>${task.id}</td><td>${esc(task.type)}</td><td class="q">${esc(task.question)}</td>`;
    for (const sys of SYSTEMS) for (const seed of [0, 1, 2]) html += cell(task.runs[sys][seed]);
    html += cell(task.runs.rag[0]) + "</tr>";
  }
  $("#grid").innerHTML = html + "</tbody>";
  for (const row of document.querySelectorAll("tr.task")) row.onclick = () => { location.hash = "task=" + row.dataset.id; };
}

const DASH = "[-\u2010-\u2014\u2212]";  // the evaluation treats Unicode dashes as hyphens
const DATE = new RegExp(`^\\d{4}${DASH}\\d{2}${DASH}\\d{2}$`);
const TOKEN = new RegExp(`(?<![\\w.\u2010-\u2014\u2212-])(\\d{4}${DASH}\\d{2}${DASH}\\d{2}|\\d[\\d,]*(?:\\.\\d+)?)(?![\\w])`, "g");

function highlightAnswer(run) {
  const has = (list, value) => list.some((x) => x === value);
  return esc(run.answer).replace(TOKEN, (token) => {
    if (DATE.test(token)) return has(run.direct, token.replace(new RegExp(DASH, "g"), "-")) ? `<mark class="found">${token}</mark>` : token;
    const value = parseFloat(token.replace(/,/g, ""));
    if (has(run.unsupported, value)) return `<mark class="unsupported" title="not found in the tool outputs; judged unsupported">${token}</mark>`;
    if (has(run.checked_by_hand, value)) return `<mark class="hand" title="not found verbatim; checked by hand (for example, derived)">${token}</mark>`;
    if (has(run.direct, value)) return `<mark class="found" title="found in the question or tool outputs">${token}</mark>`;
    if (run.not_found && has(run.not_found, value)) return `<mark class="unsupported" title="not found in the question or tool outputs; check it">${token}</mark>`;
    return token;
  });
}

function highlightInjection(text, payload) {
  if (!payload || !text.includes(payload)) return esc(text);
  return text.split(payload).map(esc).join(`<mark class="injected" title="text inserted by the injection test">${esc(payload)}</mark>`);
}

function renderRun(task, sys, seed) {
  const run = task.runs[sys][sys === "rag" ? 0 : seed];
  if (!run) return "<p>No run.</p>";
  const cls = run.success === null ? "neutral" : run.success ? "ok" : "bad";
  const payload = task.injection && task.injection.payload;
  let html = `<div class="verdict ${cls}">${run.success === null ? "Graded " + esc(run.correctness) : esc(reasonText(run))}</div>`;
  html += `<p class="meta">Correctness: ${esc(run.correctness)} (${esc(run.label_source)}) · caveat stated: ${run.caveat ? "yes" : "no"}`;
  if (task.injection) html += ` · injection seen: ${run.injection_seen ? "yes" : "no"}, followed: ${run.injection_followed ? "yes" : "no"}`;
  html += ` · ${run.seconds.toFixed(1)} s · ${run.prompt_tokens} input / ${run.output_tokens} output tokens · stop: ${esc(run.stop)}</p>`;
  let answer = highlightAnswer(run);
  const canary = task.injection && task.injection.detector.kind === "answer_contains" ? esc(task.injection.detector.value) : "";
  if (canary) answer = answer.split(canary).join(`<mark class="injected" title="the injection's canary string">${canary}</mark>`);
  html += `<h3>Answer</h3><div class="answer">${answer}</div>`;
  return html + renderTrace(run, payload, false);
}

// Shared with the local service's page (live.js), which builds the same run object from the event stream.
function renderTrace(run, payload, open) {
  let html = `<details${open ? " open" : ""}><summary>Trace: ${run.turns.length} model turns, ${run.turns.reduce((n, t) => n + t.tool_calls.length, 0)} tool calls</summary>`;
  run.turns.forEach((turn, i) => {
    html += `<div class="step"><div class="meta">Model turn ${i + 1}</div>`;
    if (turn.thinking) html += `<details><summary>Reasoning</summary><pre>${esc(turn.thinking)}</pre></details>`;
    if (turn.content) html += `<pre>${esc(turn.content)}</pre>`;
    for (const call of turn.tool_calls) {
      html += `<div><span class="call-name">${esc(call.name)}</span> <code>${esc(JSON.stringify(call.args))}</code>` +
        `${call.is_error ? ' <span class="error">error</span>' : ""}</div>`;
      if (call.output !== undefined) html += `<details${payload && call.output.includes(payload) ? " open" : ""}><summary>Output</summary><pre>${highlightInjection(call.output, payload)}</pre></details>`;
    }
    html += "</div>";
  });
  return html + "</details>";
}

function picker(side, sys, seed) {
  const options = [...SYSTEMS.flatMap((s) => [0, 1, 2].map((k) => [`${s}:${k}`, `${LABEL[s]} run ${k + 1}`])), ["rag:0", "RAG baseline"]];
  return `<select data-side="${side}">${options.map(([v, l]) => `<option value="${v}"${v === `${sys}:${seed}` ? " selected" : ""}>${l}</option>`).join("")}</select>`;
}

function renderDetail(id) {
  const task = DATA.tasks.find((t) => t.id === id);
  if (!task) { location.hash = ""; return; }
  const state = { left: ["gemma", 0], right: ["gpt-oss", 0] };
  const draw = () => {
    let html = `<p class="back"><a href="#">← All tasks</a></p><h2>${task.id}: ${esc(task.question)}</h2>`;
    html += `<p class="meta">Type: ${esc(task.type)} · caveat required: ${task.requires_caveat ? "yes" : "no"}</p>`;
    if (task.injection) html += `<div class="box">Injection test: the text <mark class="injected">${esc(task.injection.payload)}</mark> was inserted into ` +
      `<code>${esc(task.injection.target.tool)}</code> output, field <code>${esc(task.injection.target.field)}</code>.</div>`;
    html += `<details><summary>Reference answer</summary><div class="box">${esc(task.reference)}</div></details>`;
    html += `<p class="legend">Numbers in answers: <mark class="found">found in the tool outputs</mark> · <mark class="hand">not found verbatim, checked by hand</mark> · ` +
      `<mark class="unsupported">unsupported</mark>. Answers are shown as the model wrote them (Markdown source). Highlighting is approximate; the evaluation's check is authoritative.</p><div class="columns">`;
    for (const side of ["left", "right"]) {
      const [sys, seed] = state[side];
      html += `<div class="panel"><div class="pick">${picker(side, sys, seed)}</div>${renderRun(task, sys, seed)}</div>`;
    }
    $("#detail").innerHTML = html + "</div>";
    for (const sel of document.querySelectorAll("#detail select")) sel.onchange = () => {
      const [sys, seed] = sel.value.split(":");
      state[sel.dataset.side] = [sys, Number(seed)];
      draw();
    };
  };
  draw();
  $("#overview").hidden = true;
  $("#detail").hidden = false;
  window.scrollTo(0, 0);
}

function route() {
  const match = location.hash.match(/^#task=(\w+)$/);
  if (match) renderDetail(match[1]);
  else { $("#detail").hidden = true; $("#overview").hidden = false; }
}

if ($("#grid")) fetch("data.json").then((r) => r.json()).then((data) => {
  DATA = data;
  renderSummary();
  for (const type of [...new Set(DATA.tasks.map((t) => t.type))].sort()) $("#filter-type").insertAdjacentHTML("beforeend", `<option>${esc(type)}</option>`);
  $("#filter-type").onchange = renderGrid;
  $("#filter-outcome").onchange = renderGrid;
  renderGrid();
  window.onhashchange = route;
  route();
}).catch((err) => { $("#summary").textContent = "Could not load data.json: " + err; });
