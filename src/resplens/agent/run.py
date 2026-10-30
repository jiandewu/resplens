"""Run the A3 agent on a split of eval/tasks.jsonl, and score the traces (plan: docs/agent-eval.md).

    uv run --extra models python -m resplens.agent.run run --split dev --system gemma --seed 0
    uv run python -m resplens.agent.run score eval/agent-runs/<run>
    uv run python -m resplens.agent.run mcp-check eval/agent-runs/<run> --tasks a01,a02,a09
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from .. import server
from ..data import DATA_TAG
from ..retrieval.dense import OLLAMA_URL
from ..retrieval.evaluate import ROOT, _git_commit
from . import checks, loop


TASKS = ROOT / "eval" / "tasks.jsonl"
RUN_INPUTS = ["src", "corpus", "eval/tasks.jsonl", "pyproject.toml", "uv.lock"]
# Reasoning settings chosen on dev 2026-10-30 and fixed (docs/agent-eval.md); --think overrides for dev runs only.
SYSTEMS = {"gemma": {"model": "gemma4:31b", "think": False},
           "gpt-oss": {"model": "gpt-oss:120b", "think": "medium"}}


def load_tasks(split: str, ids: list[str] | None = None) -> list[dict]:
    rows = [json.loads(line) for line in TASKS.read_text().splitlines() if line.strip()]
    return [row for row in rows if row["split"] == split and (not ids or row["id"] in ids)]


def _ollama(path: str, body: dict | None = None) -> dict:
    request = urllib.request.Request(f"{OLLAMA_URL}{path}", json.dumps(body).encode() if body else None,
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def model_info(model: str) -> dict:
    tags = {m["name"]: m["digest"] for m in _ollama("/api/tags")["models"]}
    return {"model": model, "digest": tags.get(model), "ollama_version": _ollama("/api/version")["version"]}


def parse_think(value: str) -> bool | str:
    return {"true": True, "false": False}.get(value.lower(), value)


async def _run(split: str, system: str, seed: int, think: bool | str, ids: list[str] | None,
               system_prompt: str, resume: Path | None) -> Path:
    tasks = load_tasks(split, ids)
    model = SYSTEMS[system]["model"]
    if resume:
        run_dir = resume
        config = json.loads((run_dir / "config.json").read_text())
        model, think, seed, system_prompt = config["model"], config["think"], config["seed"], config["system_prompt"]
    else:
        run_dir = ROOT / "eval" / "agent-runs" / f"{datetime.now():%Y%m%d-%H%M%S}-{split}-{system}-seed{seed}"
        run_dir.mkdir(parents=True)
    out = run_dir / "traces.jsonl"
    done = {json.loads(line)["id"] for line in out.read_text().splitlines()} if out.exists() else set()
    async with Client(server.mcp) as client:
        toolbox = await loop.Toolbox.create(client)
        if not resume:
            config = {"split": split, "system": system, **model_info(model), "think": think, "seed": seed,
                      "temperature": 0, "num_ctx": loop.NUM_CTX, "max_output": loop.MAX_OUTPUT,
                      "num_thread": loop.CPU_THREADS,
                      "max_turns": loop.MAX_TURNS, "max_tool_calls": loop.MAX_TOOL_CALLS,
                      "system_prompt": system_prompt, "tools": toolbox.schemas,
                      "search": {"top_k": loop.SEARCH_TOP_K, "chunk_tokens": loop.CHUNK_TOKENS,
                                 "retrieval": "hybrid bm25 + BAAI/bge-m3, rerank BAAI/bge-reranker-v2-m3"},
                      "data_release": DATA_TAG,
                      "corpus_manifest_sha256": hashlib.sha256((ROOT / "corpus" / "manifest.csv").read_bytes())
                      .hexdigest(),
                      "task_ids": [task["id"] for task in tasks],
                      "git_commit": _git_commit(inputs=RUN_INPUTS),  # at the start, before the code can change
                      "started": datetime.now().isoformat(timespec="seconds")}
            (run_dir / "config.json").write_text(json.dumps(config, indent=1))
        with out.open("a") as handle:
            for task in tasks:
                if task["id"] in done:
                    continue
                trace = (await loop.run_task(task, toolbox, model, think, seed, system_prompt)).to_dict()
                handle.write(json.dumps(trace) + "\n")
                handle.flush()
                print(f"{task['id']} {trace['stop']} turns={trace['model_turns']} calls={trace['tool_calls']} "
                      f"{trace['seconds']:.0f}s")
    print(f"saved to {run_dir.relative_to(ROOT)}")
    return run_dir


def score(run_dir: Path) -> list[dict]:
    config = json.loads((run_dir / "config.json").read_text())
    tasks = {task["id"]: task for task in load_tasks(config["split"])}
    traces = [json.loads(line) for line in (run_dir / "traces.jsonl").read_text().splitlines() if line.strip()]
    rows = [checks.score_trace(tasks[trace["id"]], trace) for trace in traces]
    (run_dir / "scores.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    for row in rows:
        recall = row["tool_call_recall"]
        print(f"{row['id']} {row['type']:<17} {row['stop']:<10} recall {recall['matched']}/{recall['expected']} "
              f"required {len(row['required_numbers']['present'])}/{len(tasks[row['id']]['required_numbers'])} "
              f"unmatched {row['numbers']['unmatched']} "
              + (f"injection {row['injection']}" if row["injection"] else ""))
    n = len(rows)
    unanswerable = [row for row in rows if row["type"] == "unanswerable"]
    summary = {"tasks": n, "stops": dict(Counter(row["stop"] for row in rows)),
               "tool_call_recall": round(sum(r["tool_call_recall"]["matched"] for r in rows)
                                         / max(1, sum(r["tool_call_recall"]["expected"] for r in rows)), 3),
               "direct_grounding_pass": sum(row["direct_grounding_pass"] for row in rows),
               "required_numbers_complete": sum(not row["required_numbers"]["missing"] for row in rows),
               "injection_detector_hits": sum(bool(r["injection"] and r["injection"]["detector_hit"]) for r in rows),
               "abstention_phrase_on_unanswerable":
                   f"{sum(r['abstention_phrase'] for r in unanswerable)}/{len(unanswerable)}",
               "median_seconds": sorted(row["seconds"] for row in rows)[n // 2] if rows else None}
    print(json.dumps(summary, indent=1))
    return rows


def same_output(call: dict, result) -> bool:
    """Whether an MCP result matches a recorded tool call: same structured content, or the same error text."""
    if result.is_error or result.structured_content is None:
        return call["is_error"] and bool(result.content) and result.content[0].text == call["output"]
    return not call["is_error"] and json.loads(call["output"]) == result.structured_content


async def _mcp_check(run_dir: Path, ids: list[str]) -> dict:
    """Replay a run's data-tool calls through the MCP server over stdio and compare with the in-process outputs."""
    tasks = {task["id"]: task for task in load_tasks(json.loads((run_dir / "config.json").read_text())["split"])}
    traces = [json.loads(line) for line in (run_dir / "traces.jsonl").read_text().splitlines() if line.strip()]
    params = StdioServerParameters(command=sys.executable, args=["-m", "resplens.server"], cwd=str(ROOT),
                                   env={key: os.environ[key] for key in ("RESPLENS_CACHE",) if key in os.environ})
    rows = []
    async with Client(params) as client:
        data_tools = {tool.name for tool in (await client.list_tools()).tools}
        for trace in traces:
            if trace["id"] not in ids or tasks[trace["id"]].get("injection"):  # injections alter outputs on purpose
                continue
            for turn in trace["turns"]:
                for call in turn["tool_calls"]:
                    if call["name"] in data_tools and call["args"] is not None:
                        result = await client.call_tool(call["name"], call["args"])
                        rows.append({"id": trace["id"], "tool": call["name"], "args": call["args"],
                                     "identical": same_output(call, result)})
    report = {"transport": "stdio", "command": f"{Path(sys.executable).name} -m resplens.server", "tasks": ids,
              "calls": len(rows), "identical": sum(row["identical"] for row in rows), "rows": rows}
    (run_dir / "mcp-check.json").write_text(json.dumps(report, indent=1))
    print(f"{report['identical']}/{report['calls']} data-tool calls identical over stdio")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--split", default="dev", choices=["dev", "test"])
    run.add_argument("--system", default="gemma", choices=sorted(SYSTEMS))
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--think", help="override the system's reasoning setting: false, true, low, medium, high")
    run.add_argument("--tasks", help="comma-separated task IDs (default: the whole split)")
    run.add_argument("--system-prompt", type=Path, help="file with a system prompt to try on dev")
    run.add_argument("--resume", type=Path, help="continue an interrupted run directory")
    scorer = commands.add_parser("score")
    scorer.add_argument("run_dir", type=Path)
    check = commands.add_parser("mcp-check", help="replay a run's data-tool calls over stdio and compare outputs")
    check.add_argument("run_dir", type=Path)
    check.add_argument("--tasks", required=True, help="comma-separated task IDs")
    args = parser.parse_args(argv)
    if args.command == "run":
        if args.split == "test" and (args.think or args.system_prompt):
            parser.error("test runs use the frozen settings; --think and --system-prompt are for dev only")
        think = parse_think(args.think) if args.think else SYSTEMS[args.system]["think"]
        prompt = args.system_prompt.read_text().strip() if args.system_prompt else loop.SYSTEM_PROMPT
        ids = args.tasks.split(",") if args.tasks else None
        asyncio.run(_run(args.split, args.system, args.seed, think, ids, prompt, args.resume))
    elif args.command == "score":
        score(args.run_dir)
    else:
        asyncio.run(_mcp_check(args.run_dir, args.tasks.split(",")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
