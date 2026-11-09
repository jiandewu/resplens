"use strict";
// The local service's page. It builds a run object from the event stream and renders it with replay.js.

let SYSTEMS_INFO = {};

function renderLive(run, status) {
  let html = `<p class="meta">${esc(run.model)}${run.evaluated ? "" : " (not evaluated)"}${status ? " · " + esc(status) : ""}</p>`;
  if (run.error) html += `<div class="verdict bad">${esc(run.error)}</div>`;
  if (run.answer !== undefined) {
    html += `<p class="meta">${run.seconds.toFixed(1)} s · ${run.prompt_tokens} input / ${run.output_tokens} output tokens · stop: ${esc(run.stop)}</p>`;
    html += `<p class="legend">Numbers: <mark class="found">found in the question or tool outputs</mark> · ` +
      `<mark class="unsupported">not found; derived or unsupported, check it</mark>.</p>`;
    html += `<h3>Answer</h3><div class="answer">${highlightAnswer(run)}</div>`;
  }
  html += renderTrace(run, "", run.answer === undefined);
  $("#result").innerHTML = html;
}

function apply(run, event) {
  if (event.type === "start") Object.assign(run, { model: event.model, evaluated: event.evaluated });
  else if (event.type === "model_turn") run.turns.push({ content: event.content, thinking: event.thinking, tool_calls: event.tool_calls.map((c) => ({ ...c })) });
  else if (event.type === "tool_output") {
    const turn = run.turns[run.turns.length - 1];
    const call = turn && turn.tool_calls.find((c) => c.output === undefined);
    if (call) Object.assign(call, { args: event.args, output: event.output, is_error: event.is_error });
  } else if (event.type === "answer") Object.assign(run, event, { unsupported: [], checked_by_hand: [] });
  else if (event.type === "error") run.error = event.message;
}

async function ask(question, system) {
  const run = { model: SYSTEMS_INFO[system].model, evaluated: SYSTEMS_INFO[system].evaluated, turns: [] };
  $("#result").hidden = false;
  renderLive(run, "starting");
  const response = await fetch("api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question, system }) });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    run.error = body.detail ? (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)) : `HTTP ${response.status}`;
    renderLive(run, "");
    return;
  }
  const reader = response.body.getReader(), decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let cut;
    while ((cut = buffer.indexOf("\n\n")) >= 0) {
      const line = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      if (!line.startsWith("data: ")) continue;
      const event = JSON.parse(line.slice(6));
      apply(run, event);
      const status = event.type === "model_start" ? `waiting for model turn ${run.turns.length + 1}` :
        event.type === "tool_output" ? `ran ${event.name}` : "";
      renderLive(run, status);
    }
  }
}

fetch("api/systems").then((r) => r.json()).then((systems) => {
  SYSTEMS_INFO = systems;
  for (const [name, info] of Object.entries(systems)) $("#system").insertAdjacentHTML("beforeend", `<option value="${esc(name)}">${esc(info.model)}</option>`);
  const note = () => { $("#not-evaluated").hidden = SYSTEMS_INFO[$("#system").value].evaluated; };
  $("#system").onchange = note;
  note();
});

$("#ask").onsubmit = async (e) => {
  e.preventDefault();
  $("#submit").disabled = true;
  try { await ask($("#question").value.trim(), $("#system").value); }
  catch (err) { $("#result").hidden = false; $("#result").insertAdjacentHTML("afterbegin", `<div class="verdict bad">${esc(String(err))}</div>`); }
  finally { $("#submit").disabled = false; }
};
