"""Validation runs for B2: choose the student and its training settings (plan: docs/finetune-eval.md, "Validation").

    uv run python -m resplens.finetune.validate run --name base-qwen3-4b --model qwen3-4b      # vLLM must be serving
    uv run python -m resplens.finetune.validate judge --name base-qwen3-4b                      # Ollama with the judge
    uv run python -m resplens.finetune.validate score --name base-qwen3-4b

The validation set is the 13 A3 dev tasks and the generated validation questions (dropped templates left out).
Each item runs once (seed 0, temperature 0, greedy). Scoring is the A3 task success with the B2 filter's number
check instead of the hand review: the judge grades the answer correct, every number in the answer matches the
question, a tool output or the system prompt, the caveat is stated where required, and no injection was followed.
The judge runs only on answers that pass the code checks, since the others cannot succeed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter, defaultdict
from datetime import datetime
from functools import partial
from pathlib import Path

from mcp import Client

from .. import server
from ..agent import checks, loop
from ..agent.judge import JUDGE, JudgeFailed, judge_one
from ..agent.run import RUN_INPUTS, load_tasks, model_info
from ..data import DATA_TAG
from ..retrieval.evaluate import _git_commit
from .questions import OUT, _read
from .traces import DROPPED_TEMPLATES

VALIDATION = OUT / "validation"
SEED = 0


def items() -> list[dict]:
    dev = [{**task, "source": "a3_dev"} for task in load_tasks("dev")]
    generated = [{**row, "source": "generated"} for row in _read(OUT / "questions.jsonl")
                 if row["split"] == "validation" and row["origin"] not in DROPPED_TEMPLATES]
    return dev + generated


def code_checks(task: dict, trace: dict) -> list[str]:
    row = checks.score_trace(task, trace)
    reasons = []
    if trace["stop"] != "answer":
        reasons.append(f"stop={trace['stop']}")
    outputs = [call["output"] for turn in trace["turns"] for call in turn["tool_calls"] if not call["is_error"]]
    if unmatched := checks.grounding(trace["answer"], task["question"], [loop.SYSTEM_PROMPT, *outputs])["unmatched"]:
        reasons.append(f"unmatched={unmatched}")
    if row["injection"] and row["injection"]["detector_hit"]:
        reasons.append("injection_followed")
    return reasons


async def _run(name: str, model: str, url: str | None, extra: dict) -> Path:
    run_dir = VALIDATION / name
    run_dir.mkdir(parents=True, exist_ok=True)
    out = run_dir / "traces.jsonl"
    done = {row["id"] for row in _read(out)} if out.exists() else set()
    tasks = items()
    chat = partial(loop.openai_chat, url=url)
    async with Client(server.mcp) as client:
        toolbox = await loop.Toolbox.create(client)
        config_path = run_dir / "config.json"
        if not config_path.exists():
            config_path.write_text(json.dumps({
                "name": name, "model": model, "url": url or loop.OPENAI_URL, **extra, "seed": SEED,
                "temperature": 0, "max_output": loop.MAX_OUTPUT, "max_turns": loop.MAX_TURNS,
                "max_tool_calls": loop.MAX_TOOL_CALLS, "system_prompt": loop.SYSTEM_PROMPT, "tools": toolbox.schemas,
                "data_release": DATA_TAG, "item_ids": [task["id"] for task in tasks],
                "git_commit": _git_commit(inputs=RUN_INPUTS),
                "started": datetime.now().isoformat(timespec="seconds")}, indent=1))
        with out.open("a") as handle:
            for task in tasks:
                if task["id"] in done:
                    continue
                trace = (await loop.run_task(task, toolbox, model, False, SEED, chat_fn=chat)).to_dict()
                handle.write(json.dumps(trace) + "\n")
                handle.flush()
                print(f"{name} {task['id']} {trace['stop']} calls={trace['tool_calls']} {trace['seconds']:.1f}s",
                      flush=True)
    return run_dir


def judge(name: str) -> None:
    run_dir = VALIDATION / name
    tasks = {task["id"]: task for task in items()}
    out = run_dir / "judgments.jsonl"
    done = {row["id"] for row in _read(out)} if out.exists() else set()
    info, commit = model_info(JUDGE), _git_commit(inputs=RUN_INPUTS)
    with out.open("a") as handle:
        for trace in _read(run_dir / "traces.jsonl"):
            if trace["id"] in done or code_checks(tasks[trace["id"]], trace):
                continue
            verdict = None
            for seed in (0, 1):  # as A3: one retry with another seed, then record the failure
                try:
                    verdict = judge_one(tasks[trace["id"]], trace, seed)
                    break
                except JudgeFailed as exc:
                    print(name, trace["id"], f"judge failed (seed {seed}): {exc}", flush=True)
            if verdict is None:
                verdict = {"correctness": "judge_failed", "unsupported_claims": False, "abstained": False,
                           "caveat_stated": False, "explanation": "no valid verdict after a retry", "reasoning": ""}
            handle.write(json.dumps({"id": trace["id"], **verdict, "judge": JUDGE, "judge_digest": info["digest"],
                                     "git_commit": commit}) + "\n")
            handle.flush()
            print(name, trace["id"], verdict["correctness"], flush=True)


def score(name: str) -> dict:
    """Task success per item; writes scores.jsonl and summary.json. Fails if a passing trace has no judgment."""
    run_dir = VALIDATION / name
    tasks = {task["id"]: task for task in items()}
    judged = {row["id"]: row for row in _read(run_dir / "judgments.jsonl")} \
        if (run_dir / "judgments.jsonl").exists() else {}
    rows = []
    for trace in _read(run_dir / "traces.jsonl"):
        task = tasks[trace["id"]]
        reasons = code_checks(task, trace)
        if not reasons:
            if trace["id"] not in judged:
                raise SystemExit(f"{name} {trace['id']}: passes the code checks but has no judgment")
            label = judged[trace["id"]]
            if label["correctness"] != "correct":
                reasons.append(f"judge={label['correctness']}")
            if task.get("requires_caveat") and not label["caveat_stated"]:
                reasons.append("missing_caveat")
        rows.append({"id": trace["id"], "source": task["source"], "type": task["type"], "success": not reasons,
                     "reasons": reasons, "tool_calls": trace["tool_calls"], "seconds": trace["seconds"]})
    if len(rows) != len(tasks):
        raise SystemExit(f"{name}: {len(rows)} of {len(tasks)} items run")
    (run_dir / "scores.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))

    def rate(subset):
        return {"success": sum(r["success"] for r in subset), "items": len(subset),
                "rate": round(sum(r["success"] for r in subset) / len(subset), 3) if subset else None}

    by = defaultdict(list)
    for row in rows:
        by[row["type"]].append(row)
    summary = {"name": name, "all": rate(rows),
               "a3_dev": rate([r for r in rows if r["source"] == "a3_dev"]),
               "generated": rate([r for r in rows if r["source"] == "generated"]),
               "by_type": {key: rate(value) for key, value in sorted(by.items())},
               "reasons": dict(Counter(reason.split("=")[0] for r in rows for reason in r["reasons"])),
               "median_seconds": sorted(r["seconds"] for r in rows)[len(rows) // 2]}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--name", required=True, help="run directory under eval/finetune/validation/")
    run.add_argument("--model", required=True, help="served model name")
    run.add_argument("--url", help="OpenAI-compatible server (default RESPLENS_OPENAI_URL)")
    run.add_argument("--info", default="{}", help="JSON recorded in config.json (base repo, revision, vLLM version)")
    for command in ("judge", "score"):
        commands.add_parser(command).add_argument("--name", required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        asyncio.run(_run(args.name, args.model, args.url, json.loads(args.info)))
    elif args.command == "judge":
        judge(args.name)
    else:
        print(json.dumps(score(args.name), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
