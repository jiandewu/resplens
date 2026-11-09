# A4: running the agent locally, and a public replay of the evaluated runs

Status: **reviewed by the author 2026-11-06** (decisions at the end). B (the replay) is implemented in `src/resplens/app/replay.py` and published on GitHub Pages; A (the local service) in `src/resplens/app/service.py` (2026-11-09).

## Goal

Two ways to see the A3 agent work, at no cost:

- **A. Local service**: one command starts the agent with a web page and an HTTP API on the user's own machine, against a local Ollama. Each query is logged with latency, tokens and tool calls.
- **B. Public replay**: a static web page that shows the A3 test runs as they were recorded: question, every model turn and tool call, the tool outputs, the answer, the automatic number check, the grades, and the injection tasks. Nothing is computed live, so it costs nothing, cannot be abused, and shows exactly the runs that `docs/agent-results.md` reports.

Not in scope: a live public demo. Docker Spaces on Hugging Face need a paid plan (PRO, $9/month, per the Spaces docs read 2026-11-06), and NVIDIA's trial API allows "internal testing and evaluation purposes, not in production" (NVIDIA API Trial Terms of Service, section 1.4), so a public live demo needs a paid model API. That is a later decision; the service in A is written so that only the model backend and the host change.

## Why replay first

- Anyone with the link sees the agent's behavior in seconds, with no cold start and no hardware.
- It shows failures as well as successes, with the grades from the evaluation, so it cannot overstate the results.
- It needs no model and no change to the evaluated code, so it can be built while other evaluation runs use the machine.

## B. Public replay

**Content** (all files already in the public repository):

- the 24 test tasks (`eval/tasks.jsonl`), with their type, whether a caveat is required, and the injection (where the payload was inserted);
- the six agent runs (gemma and gpt-oss, seeds 0-2) and the RAG-only baseline (`eval/agent-runs/2026103*-test-*/traces.jsonl`);
- per agent run and task, the scores in `eval/agent-review/rows.jsonl` (144 rows): author grades for seed 0, judge grades for all seeds, unsupported numbers, injection seen and followed, and tool-call recall. Task success is computed with the same function as the results (`agent.analyze.success`), not re-implemented. The RAG baseline is not in `rows.jsonl`: it is shown with its judge labels from its run directory, and the page states, as `docs/agent-results.md` does, that 4 refusals the judge accepted as correct (`b01`, `b03`, `b06`, `b10`) were counted as not correct by hand after unblinding (11/24 to 7/24 correct), and that the baseline ran without injections.

Dev runs are left out; the page shows only what the results report.

**Page**:

- A grid of tasks by system and seed, each cell showing success or the reason for failure (wrong, unsupported number, missing caveat, injection followed). Filters by task type, system, seed and outcome.
- A task view: the question, then each system's trace side by side: model turns (with the reasoning text collapsed), tool calls with arguments, tool outputs collapsed and expandable, and the final answer. Numbers in the answer are highlighted as found or not found in the tool outputs, using the same check as the evaluation (`agent/checks.py`). In injection tasks the inserted text is highlighted where it appears in a tool output.
- A short header with the main result and a link to `docs/agent-results.md`, and a note that these are recorded runs, not live answers.

**Build**: `python -m resplens.app.replay --out site/` reads the files above and writes `site/index.html`, a stylesheet, one script, and `site/data.json` (about 2 MB). No framework and no build step. Recomputing the number check at build time must give the same unsupported numbers as `rows.jsonl`; the build stops if any differ.

**Hosting**: GitHub Pages on the public repository, built by a GitHub Actions workflow from the files in `main` (no generated files committed). Alternative: a free static Hugging Face Space. GitHub Pages keeps the page next to the code and needs no other account.

## A. Local service

**Pieces** (new package `src/resplens/app/`, optional dependency group `app`: FastAPI, uvicorn):

- `POST /api/ask` with a question and a system (`gemma` or `gpt-oss`, the A3 settings). It runs the unchanged A3 loop (`agent.loop.run_task`) with the A3 system prompt and tools, and streams events (model turn, tool call, tool output, answer) as server-sent events. The streaming comes from wrapping the loop's existing `chat_fn` and `Toolbox.call` hooks; `loop.py` is not changed, so the evaluated behavior is the behavior served.
- After the answer, the number check (`checks.grounding`) runs on the answer and the tool outputs, and the page highlights unsupported numbers as in the replay.
- `GET /healthz` returns 200 without calling a model.
- The page is the replay's task view fed by the live event stream, so one renderer serves both.
- One question at a time (a lock); a question limit of 1,000 characters.
- **Query log**: one JSON line per query in `logs/queries.jsonl` (git-ignored): time, system, model and digest, seconds, prompt and output tokens, model turns, tool names and errors, stop reason, and numbers found and not found. The question text is logged too, since the service runs on the user's own machine; a setting turns that off.

**Running it**:

- Without containers: `uv sync --extra app --extra models`, start Ollama, `uv run resplens-app`.
- With containers (deferred, see decisions): a `Dockerfile` for the app (CPU PyTorch for the retrieval models) and a `compose.yaml` with the app and the official Ollama image. Volumes keep the data release, the retrieval models and the Ollama models between runs. The first start downloads the data release (checked against its SHA-256 as now), the two retrieval models and the chosen LLM.
- Hardware, stated in the README: the evaluated models are large (gemma4:31b and gpt-oss:120b). Their memory needs are to be measured, not quoted. Another Ollama model can be set with an environment variable, and the page then says that this model was not evaluated.

**Tests** (no model, no network): the API with a scripted fake model (events in order, the lock, the length limit, `healthz`); the log line; the replay builder on a small fixture, including the check that recomputed unsupported numbers match the stored ones.

**Demo GIF**: recorded from the local service on one dev task, not a test task, so the GIF does not show a result that was not in the evaluation.

## Order

1. Replay builder and page (B); code kept out of `src/` while other evaluation runs were in progress, since those runs record whether `src/` is clean.
2. Local service and its tests (A), then a live check with Ollama.
3. Dockerfile and compose: deferred until a machine with Docker is available (see decisions).
4. README section, GIF, interview-prep.

## Decisions (author, 2026-11-06)

1. The replay is hosted on GitHub Pages from the public repository.
2. The replay may be released to the public repository on its own, ahead of other work, since it shows only files that are already public.
3. Containers are not built for now. This cluster node has no Docker, and it cannot be installed: there is no root access, and rootless Docker or Podman needs subordinate user IDs (`/etc/subuid`), which this account does not have. The local service ships with the `uv` route only; the Dockerfile and compose file wait until there is a machine with Docker to test them on, since an untested Dockerfile would not be shipped.

## Implementation notes (2026-11-09)

- **Service**: `POST /api/ask` streams JSON events (`start`, `model_start`, `model_turn`, `tool_output`, `answer`, or `error`). The loop runs in a worker thread with its own event loop and an in-process MCP client; events pass through a queue. A second question while one runs gets HTTP 429. If the browser disconnects, the running question still finishes and is logged. A failed query is reported on the page and not logged.
- **Systems**: `gemma` and `gpt-oss` with the A3 settings and seed 0 (the evaluation's first run); `RESPLENS_OTHER_MODEL` adds one more, thinking off, marked as not evaluated.
- **Page**: `live.html` and `live.js` build the same run object as the replay and draw it with the replay's renderer (`renderTrace`, `highlightAnswer` in `replay.js`). Numbers not found in the question or tool outputs are marked; there is no hand review, so the page says "derived or unsupported, check it".
- **Tests** (`tests/test_service.py`, scripted fake model, synthetic mirror): event order, number check and log line; question text left out of the log; 429 while busy; length and system checks; a model failure reported and the lock released; `healthz`, systems list and page served without a model.
- **Live check** (gemma, Ollama 0.40.13, two H100 GPUs): dev tasks `a01` (3 tool calls, 15 s, 11 numbers all found), `a07` (`search_docs`, 53 s including loading the retrieval models), and `a03` through the page in headless Chromium (no script errors; no horizontal scroll at 390 px). A second request during `a07` returned 429. The replay page was rechecked after the shared renderer change: same grid counts, no script errors.
- **Memory** (Ollama `/api/ps`, 32k context): `gemma4:31b` 20.9 GB, `gpt-oss:120b` 64.5 GB, all on GPU.
- **Demo GIF** (`docs/img/local-service.gif`, 153 KB): dev task `a01` with gemma, captured from the page in headless Chromium and assembled with Pillow.

