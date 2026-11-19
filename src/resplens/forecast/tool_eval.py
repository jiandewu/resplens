"""Forecast tool evaluation (plan: docs/forecast-tool-eval.md): runs, checks, judge, blind sheets and analysis.

    uv run --extra forecast --extra models python -m resplens.forecast.tool_eval run --split dev --system gemma --seed 0
    uv run --extra forecast --extra models python -m resplens.forecast.tool_eval run --split dev --system b2-ft \
        --seed 0 --url http://127.0.0.1:8102 --info '{...}'
    uv run python -m resplens.forecast.tool_eval score eval/forecast-tool/runs/<run>
    uv run python -m resplens.forecast.tool_eval judge eval/forecast-tool/runs/<run>
    uv run python -m resplens.forecast.tool_eval review eval/forecast-tool/runs/<run> [...]
    uv run python -m resplens.forecast.tool_eval analyze

Runs use the A3 loop and limits with ForecastToolbox and forecast_prompt(); the checks, judge, blind sheets and
analysis are the A3 ones with the forecast task set, a forecast rule added to the judge prompt, and the plan's extra
success conditions (forecast calls made, forbidden calls avoided, required numbers present).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
from datetime import datetime
from functools import partial
from pathlib import Path

from ..data import DATA_TAG
from ..retrieval.evaluate import ROOT, _git_commit

TASKS = ROOT / "eval" / "forecast-tool" / "tasks.jsonl"
OUTPUTS = ROOT / "eval" / "forecast-tool" / "tool-outputs.json"
RUNS = ROOT / "eval" / "forecast-tool" / "runs"
REVIEW = ROOT / "eval" / "forecast-tool" / "review"
SYSTEMS = ("gemma", "gpt-oss", "b2-base", "b2-ft")
PAIR = ("gemma", "b2-ft")  # primary, pre-specified: the fine-tuned E4B against gemma4:31b
THOUSANDS = re.compile(r"(?<![\d.])\d{1,3}(?:[\u202f\u00a0]\d{3})+(?![\d])")
FORECAST_JUDGE_RULE = """- For an answer that reports a forecast of future weeks: correctness requires the target weeks, \
medians and 95% intervals as the forecast tool returned them (or as in the reference). caveat_stated is true only if \
the answer (1) says the numbers are a model forecast, (2) gives the model's backtest accuracy from the tool output \
(for example the 95% interval coverage), and (3) gives the reference's "Required caveat" for each forecast. The \
reference's "Optional notes" are not required.
"""
RUBRIC = ("the rubric in docs/forecast-tool-eval.md (for a forecast, caveat_stated = yes only if the answer says it is "
          "a model forecast, gives the backtest accuracy, and gives the reference's Required caveat; Optional notes are "
          "not required)")


def load_tasks(split: str | None = None) -> list[dict]:
    rows = [json.loads(line) for line in TASKS.read_text().splitlines() if line.strip()]
    return [row for row in rows if split is None or row["split"] == split]


def run_inputs() -> list[str]:
    from ..agent.run import RUN_INPUTS
    return [*RUN_INPUTS, "eval/forecast-tool/tasks.jsonl", "eval/forecast-tool/tool-outputs.json"]


def judge_prompt() -> str:
    from ..agent.judge import JUDGE_PROMPT
    anchor = "\n\nReturn JSON only."
    assert JUDGE_PROMPT.count(anchor) == 1
    return JUDGE_PROMPT.replace(anchor, "\n" + FORECAST_JUDGE_RULE + "\nReturn JSON only.")


async def run(split: str, system: str, seed: int, ids: list[str] | None, resume: Path | None, url: str | None,
              info: dict | None, variant: str | None = None) -> Path:
    from mcp import Client

    from .. import server
    from ..agent import loop
    from ..agent.run import SYSTEMS as SPECS, model_info
    from .tool import PROMPT_VARIANT, Forecaster, forecast_prompt, make_toolbox_class
    if split == "test" and variant not in (None, PROMPT_VARIANT):
        raise SystemExit("test runs use the chosen prompt variant (tool.PROMPT_VARIANT)")
    tasks = [t for t in load_tasks(split) if not ids or t["id"] in ids]
    if resume:
        run_dir = resume
        config = json.loads((run_dir / "config.json").read_text())
        system, seed, url = config["system"], config["seed"], config.get("url")
        variant = config.get("prompt_variant", "v1")
    else:
        variant = variant or PROMPT_VARIANT
        run_dir = RUNS / f"{datetime.now():%Y%m%d-%H%M%S}-{split}-{system}-seed{seed}-p{variant}"
        run_dir.mkdir(parents=True)
    spec = SPECS[system]
    vllm = spec.get("backend") == "vllm"
    chat_fn = partial(loop.openai_chat, url=url) if vllm else loop.chat
    prompt = forecast_prompt(variant)
    out = run_dir / "traces.jsonl"
    done = {json.loads(line)["id"] for line in out.read_text().splitlines()} if out.exists() else set()
    toolbox_class = make_toolbox_class()
    toolbox_class.forecaster = Forecaster()
    async with Client(server.mcp) as client:
        toolbox = await toolbox_class.create(client)
        if not resume:
            served = {"model": spec["model"], "url": url or loop.OPENAI_URL, **(info or {})} if vllm \
                else model_info(spec["model"])
            config = {"split": split, "system": system, **served, "think": spec["think"], "seed": seed,
                      "temperature": 0, "num_ctx": loop.NUM_CTX, "max_output": loop.MAX_OUTPUT,
                      "num_thread": loop.CPU_THREADS, "max_turns": loop.MAX_TURNS,
                      "max_tool_calls": loop.MAX_TOOL_CALLS, "prompt_variant": variant, "system_prompt": prompt, "tools": toolbox.schemas,
                      "data_release": DATA_TAG,
                      "tool_outputs_sha256": hashlib.sha256(OUTPUTS.read_bytes()).hexdigest(),
                      "task_ids": [task["id"] for task in tasks], "git_commit": _git_commit(inputs=run_inputs()),
                      "started": datetime.now().isoformat(timespec="seconds")}
            (run_dir / "config.json").write_text(json.dumps(config, indent=1))
        with out.open("a") as handle:
            for task in tasks:
                if task["id"] in done:
                    continue
                trace = (await loop.run_task(task, toolbox, spec["model"], spec["think"], seed, prompt,
                                             chat_fn=chat_fn)).to_dict()
                handle.write(json.dumps(trace) + "\n")
                handle.flush()
                print(f"{task['id']} {trace['stop']} turns={trace['model_turns']} calls={trace['tool_calls']} "
                      f"{trace['seconds']:.0f}s", flush=True)
    print(f"saved to {run_dir.relative_to(ROOT)}")
    return run_dir


def check(task: dict, trace: dict, prompt: str, expected_outputs: dict) -> dict:
    """The A3 checks plus the plan's: system prompt as a number source (B2 variant), forecast calls made, forbidden
    calls avoided, required numbers present, and whether each forecast output equals the recorded one."""
    from ..agent import checks
    # Thousands separated by a narrow or no-break space (gpt-oss: "1\u202f086") are one number (dev, 2026-11-17).
    trace = {**trace, "answer": THOUSANDS.sub(lambda m: re.sub(r"\D", "", m.group()), trace["answer"])}
    row = checks.score_trace(task, trace)
    # Error messages from tools are outputs the model saw (dev, 2026-11-17: "fewer than 26 reported weeks among the
    # last 52"), and the system prompt is a source as in B2.
    errors = [call["output"] for turn in trace["turns"] for call in turn["tool_calls"] if call["is_error"]]
    prompt_numbers = checks._pool([prompt, *errors])[1]
    error_dates = checks._pool(errors)[0]
    unmatched = [n for n in row["numbers"]["unmatched"]
                 if not (n in prompt_numbers if isinstance(n, float) else n in error_dates)]
    row["numbers"] = {**row["numbers"], "unmatched": unmatched}
    row["direct_grounding_pass"] = not unmatched
    calls = [call for turn in trace["turns"] for call in turn["tool_calls"]]
    wanted = [c for c in task["expected_calls"] if c["tool"] == "forecast_admissions"]
    missing = [c["args"] for c in wanted if not any(checks.call_matches(c, call) for call in calls)]
    forbidden = sorted({call["name"] for call in calls for f in task.get("forbidden_calls", [])
                        if call["name"] == f["tool"]})
    mismatch = []
    for call in calls:
        if call["name"] == "forecast_admissions" and not call["is_error"]:
            output = json.loads(call["output"])
            key = f"{output['state']}-{output['pathogen']}"
            if key in expected_outputs and output["forecasts"] != expected_outputs[key]["forecasts"]:
                mismatch.append(key)
    extra = []
    if missing:
        extra.append(f"forecast_call_missing={missing}")
    if forbidden:
        extra.append(f"forbidden_call={forbidden}")
    if row["required_numbers"]["missing"]:
        extra.append(f"required_numbers_missing={row['required_numbers']['missing']}")
    return {**row, "forecast_calls_missing": missing, "forbidden_calls_made": forbidden,
            "forecast_output_mismatch": mismatch, "extra_failures": extra}


def score(run_dir: Path) -> list[dict]:
    config = json.loads((run_dir / "config.json").read_text())
    tasks = {task["id"]: task for task in load_tasks()}
    expected = json.loads(OUTPUTS.read_text())["outputs"]
    traces = [json.loads(line) for line in (run_dir / "traces.jsonl").read_text().splitlines() if line.strip()]
    rows = [check(tasks[trace["id"]], trace, config["system_prompt"], expected) for trace in traces]
    (run_dir / "scores.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    for row in rows:
        print(f"{row['id']} {row['type']:<19} {row['stop']:<10} recall {row['tool_call_recall']['matched']}/"
              f"{row['tool_call_recall']['expected']} unmatched {row['numbers']['unmatched']} "
              f"{' '.join(row['extra_failures'])}"
              + (f" injection {row['injection']}" if row["injection"] else "")
              + (f" OUTPUT MISMATCH {row['forecast_output_mismatch']}" if row["forecast_output_mismatch"] else ""))
    print(f"{len(rows)} tasks; code checks pass (grounding and extra conditions): "
          f"{sum(r['direct_grounding_pass'] and not r['extra_failures'] for r in rows)}")
    return rows


def judge(run_dir: Path) -> None:
    from ..agent import judge as a3_judge
    from ..agent.run import model_info
    commit = _git_commit(inputs=run_inputs())
    info = model_info(a3_judge.JUDGE)
    prompt = judge_prompt()
    tasks = {task["id"]: task for task in load_tasks()}
    traces = [json.loads(line) for line in (run_dir / "traces.jsonl").read_text().splitlines() if line.strip()]
    out = run_dir / "judgments.jsonl"
    done = {json.loads(line)["id"] for line in out.read_text().splitlines()} if out.exists() else set()
    with out.open("a") as handle:
        for trace in traces:
            if trace["id"] in done:
                continue
            verdict = None
            for seed in (0, 1):  # as in A3: one retry with another seed, then record the failure
                try:
                    verdict = a3_judge.judge_one(tasks[trace["id"]], trace, seed, prompt=prompt)
                    break
                except a3_judge.JudgeFailed as exc:
                    print(trace["id"], f"judge failed (seed {seed}): {exc}")
            if verdict is None:
                verdict = {"correctness": "judge_failed", "unsupported_claims": False, "abstained": False,
                           "caveat_stated": False, "explanation": "no valid verdict after a retry", "reasoning": ""}
            handle.write(json.dumps({"id": trace["id"], **verdict, "judge": a3_judge.JUDGE,
                                     "judge_digest": info["digest"], "ollama_version": info["ollama_version"],
                                     "judge_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                                     "git_commit": commit}) + "\n")
            handle.flush()
            print(trace["id"], verdict["correctness"], "caveat" if verdict["caveat_stated"] else "", flush=True)


def review(run_dirs: list[Path]) -> dict:
    from ..agent import review as a3_review
    return a3_review.build(run_dirs, REVIEW, tasks={t["id"]: t for t in load_tasks()}, rubric=RUBRIC)


def analyze() -> dict:
    from ..agent import analyze as a3
    tasks = {t["id"]: t for t in load_tasks("test")}
    rows = a3.load(REVIEW, tasks=tasks, runs_root=RUNS)
    others = [s for s in SYSTEMS if s != PAIR[0]]
    result = {"primary": a3.compare(rows, "primary", (0, 1, 2), pair=PAIR),
              "sensitivity_run1_author": a3.compare(rows, "primary", (0,), pair=PAIR),
              "sensitivity_judge_only": a3.compare(rows, "judge", (0, 1, 2), pair=PAIR),
              "descriptive_vs_gemma": {s: a3.compare(rows, "primary", (0, 1, 2), pair=(PAIR[0], s))
                                       for s in others if s != PAIR[1]},
              "stability_tasks_with_mixed_runs": a3.stability(rows, SYSTEMS),
              "judge_author_agreement_run1": a3.agreement(rows),
              "success_by_type": a3.by_type(rows),
              "secondary": a3.secondary(rows, SYSTEMS),
              "failures": a3.failures(rows)}
    (REVIEW / "analysis.json").write_text(json.dumps(result, indent=1))
    (REVIEW / "rows.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    print(json.dumps({k: v for k, v in result.items() if k != "failures"}, indent=1))
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    runner = commands.add_parser("run")
    runner.add_argument("--split", default="dev", choices=["dev", "test"])
    runner.add_argument("--system", default="gemma", choices=SYSTEMS)
    runner.add_argument("--seed", type=int, default=0)
    runner.add_argument("--tasks", help="comma-separated task IDs (default: the whole split)")
    runner.add_argument("--resume", type=Path)
    runner.add_argument("--url", help="vLLM server for the b2 systems")
    runner.add_argument("--info", default="{}", help="JSON recorded in config.json for the b2 systems")
    runner.add_argument("--prompt-variant", help="forecast rule variant to try on dev (tool.FORECAST_RULES)")
    for name in ("score", "judge"):
        commands.add_parser(name).add_argument("run_dir", type=Path)
    commands.add_parser("review").add_argument("run_dirs", nargs="+", type=Path)
    commands.add_parser("analyze")
    args = parser.parse_args(argv)
    if args.command == "run":
        asyncio.run(run(args.split, args.system, args.seed, args.tasks.split(",") if args.tasks else None,
                        args.resume, args.url, json.loads(args.info), args.prompt_variant))
    elif args.command == "score":
        score(args.run_dir)
    elif args.command == "judge":
        judge(args.run_dir)
    elif args.command == "review":
        review(args.run_dirs)
    else:
        analyze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
