"""Teacher traces for B2: run, filter, select, and convert to training data (plan: docs/finetune-eval.md, "Traces").

    uv run --extra models python -m resplens.finetune.traces run --teacher gemma      # resumable
    uv run --extra models python -m resplens.finetune.traces run --teacher gpt-oss
    uv run python -m resplens.finetune.traces judge     # the judge, only for traces that pass the code checks
    uv run python -m resplens.finetune.traces select    # filter, edit injected text, pick one trace per question
    uv run python -m resplens.finetune.traces review    # the kept and rejected traces the author reads

Teachers use the A3 settings (system prompt v1, tools, step limits, temperature 0, seed 0). Only training questions
get teacher traces; validation questions are for choosing the student and its training settings.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from mcp import Client

from .. import server
from ..agent import checks, loop
from ..agent.judge import JUDGE, JudgeFailed, judge_one
from ..agent.run import RUN_INPUTS, SYSTEMS, model_info
from ..retrieval.evaluate import _git_commit
from .questions import OUT, _read

TRACES = OUT / "traces"
SELECT_SEED = 20261109


# Templates dropped after the teacher runs (the author, 2026-11-11). The rows stay in questions.jsonl so IDs, and
# the traces keyed by them, do not change. lookup_sites: describe_state lists the sites without a count, so the
# answer is a count of a list, which the strict number check cannot accept.
DROPPED_TEMPLATES = ("template:lookup_sites",)


def questions(split: str = "train") -> list[dict]:
    return [row for row in _read(OUT / "questions.jsonl")
            if row["split"] == split and row["origin"] not in DROPPED_TEMPLATES]


def grounding(task: dict, trace: dict, answer: str) -> dict:
    """The strict A3 number check, with the system prompt also counted as a source: the student sees it too, and
    an answer restating its "50 states and DC" is grounded (the author, 2026-11-11). A3 scoring is unchanged."""
    outputs = [call["output"] for turn in trace["turns"] for call in turn["tool_calls"] if not call["is_error"]]
    return checks.grounding(answer, task["question"], [loop.SYSTEM_PROMPT, *outputs])


async def _run(teacher: str, rows: list[dict]) -> Path:
    out_dir = TRACES / teacher
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "traces.jsonl"
    done = {row["id"] for row in _read(out)} if out.exists() else set()
    spec = SYSTEMS[teacher]
    config_path = out_dir / "config.json"
    if not config_path.exists():
        config_path.write_text(json.dumps({"teacher": teacher, **model_info(spec["model"]), "think": spec["think"],
                                           "seed": 0, "temperature": 0, "system_prompt": loop.SYSTEM_PROMPT,
                                           "max_turns": loop.MAX_TURNS, "max_tool_calls": loop.MAX_TOOL_CALLS,
                                           "git_commit": _git_commit(inputs=RUN_INPUTS),
                                           "started": datetime.now().isoformat(timespec="seconds")}, indent=1))
    async with Client(server.mcp) as client:
        toolbox = await loop.Toolbox.create(client)
        with out.open("a") as handle:
            for row in rows:
                if row["id"] in done:
                    continue
                trace = (await loop.run_task(row, toolbox, spec["model"], spec["think"], 0)).to_dict()
                handle.write(json.dumps(trace) + "\n")
                handle.flush()
                print(f"{teacher} {row['id']} {trace['stop']} calls={trace['tool_calls']} {trace['seconds']:.0f}s",
                      flush=True)
    return out


DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def reliability_window(task: dict, trace: dict) -> bool:
    """Added after the author's trace review (2026-11-13): if the question names a date and the trace calls
    check_reliability, at least one returned window must contain that date. gpt-oss often left out `end`, got the
    latest four weeks, and stated them as the reliability of the week asked about. Unanswerable questions are
    exempt (a refusal for a future week can check the latest window)."""
    dates = set(DATE.findall(task["question"]))
    calls = [call for turn in trace["turns"] for call in turn["tool_calls"]
             if call["name"] == "check_reliability" and not call["is_error"]]
    if task["type"] == "unanswerable" or not dates or not calls:
        return True
    for call in calls:
        try:
            window = json.loads(call["output"])["window"]
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        if any(window["start"] <= day <= window["end"] for day in dates):
            return True
    return False


def code_checks(task: dict, trace: dict) -> dict:
    """The filter's checks that need no model. An answer whose only fault is a non-numeric injected string is
    edited (the string removed) and checked again (the author's decision (b), 2026-11-09)."""
    row = checks.score_trace(task, trace)
    answer, edited = trace["answer"], False
    spec = task.get("injection")
    hit = bool(row["injection"] and row["injection"]["detector_hit"])
    if hit and spec["detector"]["kind"] == "answer_contains" and not re.fullmatch(r"[\d.]+", spec["detector"]["value"]):
        answer = remove_text(answer, spec["detector"]["value"])
        edited = True
        row = checks.score_trace(task, {**trace, "answer": answer})
        hit = row["injection"]["detector_hit"]
    reasons = []
    if trace["stop"] != "answer":
        reasons.append(f"stop={trace['stop']}")
    if unmatched := grounding(task, trace, answer)["unmatched"]:
        reasons.append(f"unmatched={unmatched}")
    if row["required_numbers"]["missing"]:
        reasons.append(f"missing={row['required_numbers']['missing']}")
    if hit:
        reasons.append("injection_followed")
    if not reliability_window(task, trace):
        reasons.append("reliability_window")
    return {"pass": not reasons, "reasons": reasons, "edited": edited, "answer": answer}


def remove_text(answer: str, text: str) -> str:
    """Remove an injected string; a line left empty, or holding only punctuation, is dropped."""
    lines = []
    for line in answer.split("\n"):
        if text in line:
            line = re.sub(r"\(\s*\)|\[\s*\]|`\s*`", "", line.replace(text, ""))
            line = re.sub(r" {2,}", " ", line).replace(" .", ".").replace(" ,", ",").rstrip()
            if not re.sub(r"[\s*_`.,;:()\[\]-]", "", line):
                continue
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def judge(teachers: tuple[str, ...] = tuple(SYSTEMS)) -> None:
    tasks = {row["id"]: row for row in questions()}
    for teacher in teachers:
        path = TRACES / teacher / "traces.jsonl"
        if not path.exists():
            continue
        out = TRACES / teacher / "judgments.jsonl"
        done = {row["id"] for row in _read(out)} if out.exists() else set()
        info = model_info(JUDGE)
        with out.open("a") as handle:
            for trace in _read(path):
                if trace["id"] not in tasks:  # a dropped template
                    continue
                task = tasks[trace["id"]]
                check = code_checks(task, trace)
                if trace["id"] in done or not check["pass"]:
                    continue
                verdict = None
                for seed in (0, 1):
                    try:
                        verdict = judge_one(task, {**trace, "answer": check["answer"]}, seed)
                        break
                    except JudgeFailed as exc:
                        print(teacher, trace["id"], f"judge failed (seed {seed}): {exc}", flush=True)
                if verdict is None:
                    verdict = {"correctness": "judge_failed", "caveat_stated": False}
                handle.write(json.dumps({"id": trace["id"], "correctness": verdict["correctness"],
                                         "caveat_stated": verdict["caveat_stated"],
                                         "unsupported_claims": verdict.get("unsupported_claims"),
                                         "explanation": verdict.get("explanation", ""),
                                         "judge": JUDGE, "judge_digest": info["digest"]}) + "\n")
                handle.flush()
                print(teacher, trace["id"], verdict["correctness"], flush=True)


def select(teachers: tuple[str, ...] = tuple(SYSTEMS), seed: int = SELECT_SEED) -> dict:
    """Apply the full filter, then pick one passing trace per question at random. Writes kept.jsonl and
    filter.jsonl (every trace with its verdict) and returns counts."""
    tasks = {row["id"]: row for row in questions()}
    verdicts, passing = [], {}
    for teacher in teachers:
        path = TRACES / teacher / "traces.jsonl"
        judged = {row["id"]: row for row in _read(TRACES / teacher / "judgments.jsonl")} \
            if (TRACES / teacher / "judgments.jsonl").exists() else {}
        for trace in _read(path) if path.exists() else []:
            if trace["id"] not in tasks:  # a dropped template
                continue
            task = tasks[trace["id"]]
            check = code_checks(task, trace)
            reasons = list(check["reasons"])
            if check["pass"]:
                label = judged.get(trace["id"])
                if label is None:
                    reasons.append("not_judged")
                else:
                    if label["correctness"] != "correct":
                        reasons.append(f"judge={label['correctness']}")
                    if task["requires_caveat"] and not label["caveat_stated"]:
                        reasons.append("missing_caveat")
            verdicts.append({"id": trace["id"], "teacher": teacher, "pass": not reasons, "reasons": reasons,
                             "edited": check["edited"]})
            if not reasons:
                passing.setdefault(trace["id"], []).append({**trace, "answer": check["answer"], "teacher": teacher,
                                                            "edited": check["edited"]})
    rng = random.Random(seed)
    kept = [rng.choice(sorted(options, key=lambda t: t["teacher"])) for _, options in sorted(passing.items())]
    (OUT / "filter.jsonl").write_text("".join(json.dumps(row) + "\n" for row in verdicts))
    (OUT / "kept.jsonl").write_text("".join(json.dumps(row) + "\n" for row in kept))
    summary = {"questions": len(tasks), "traces": len(verdicts), "passing_traces": sum(v["pass"] for v in verdicts),
               "questions_kept": len(kept), "kept_by_teacher": dict(Counter(t["teacher"] for t in kept)),
               "kept_by_type": dict(Counter(tasks[t["id"]]["type"] for t in kept)),
               "edited": sum(t["edited"] for t in kept),
               "reasons": dict(Counter(r.split("=")[0] for v in verdicts for r in v["reasons"]))}
    (OUT / "select-summary.json").write_text(json.dumps(summary, indent=1))
    return summary


TRACE_REVIEW_SEED = 20261113
OUTPUT_CHARS = 1500  # tool outputs are cut in the review sheet; the full trace is in traces.jsonl


def trace_review_sample(n_kept: int = 50, n_rejected: int = 20, seed: int = TRACE_REVIEW_SEED) -> list[dict]:
    """Plan, Traces step 4: kept traces and rejected ones for the author. Kept: one from every (type, teacher) pair
    and one edited trace per teacher, the rest at random. Rejected: one from every (first reason, teacher) pair, the
    rest at random. Each row is a filter verdict; `kept` marks whether it is the trace chosen for training."""
    rng = random.Random(seed)
    tasks = {row["id"]: row for row in questions()}
    chosen = {(t["id"], t["teacher"]) for t in _read(OUT / "kept.jsonl")}
    verdicts = _read(OUT / "filter.jsonl")
    kept = [v for v in verdicts if (v["id"], v["teacher"]) in chosen]
    rejected = [v for v in verdicts if not v["pass"]]

    def draw(pool, strata, n):
        groups = {}
        for row in pool:
            for key in strata(row):
                groups.setdefault(key, []).append(row)
        picked = []
        for key in sorted(groups):
            options = [row for row in groups[key] if row not in picked]
            if options:
                picked.append(rng.choice(options))
        rest = [row for row in pool if row not in picked]
        return picked + rng.sample(rest, max(n - len(picked), 0))

    kept = draw(kept, lambda v: [(tasks[v["id"]]["type"], v["teacher"])] +
                ([("edited", v["teacher"])] if v["edited"] else []), n_kept)
    rejected = draw(rejected, lambda v: [(v["reasons"][0].split("=")[0], v["teacher"])], n_rejected)
    rows = [{**v, "kept": True} for v in kept] + [{**v, "kept": False} for v in rejected]
    return sorted(rows, key=lambda v: (not v["kept"], tasks[v["id"]]["type"], v["id"], v["teacher"]))


def _cut(text: str, limit: int = OUTPUT_CHARS) -> str:
    return text if len(text) <= limit else text[:limit] + f"\n... [{len(text) - limit} more characters]"


def trace_review_sheet(sample: list[dict]) -> str:
    tasks = {row["id"]: row for row in questions()}
    traces = {(t["id"], teacher): t for teacher in SYSTEMS if (TRACES / teacher / "traces.jsonl").exists()
              for t in _read(TRACES / teacher / "traces.jsonl")}
    judged = {(j["id"], teacher): j for teacher in SYSTEMS if (TRACES / teacher / "judgments.jsonl").exists()
              for j in _read(TRACES / teacher / "judgments.jsonl")}
    n_kept = sum(v["kept"] for v in sample)
    lines = ["# B2 trace review", "",
             f"{n_kept} kept and {len(sample) - n_kept} rejected traces (`filter.jsonl`, `kept.jsonl`), drawn with "
             f"seed {TRACE_REVIEW_SEED}. Kept: one from every (type, teacher) pair and one edited trace per teacher, "
             "the rest at random. Rejected: one from every (first reason, teacher) pair, the rest at random. "
             "Because of the strata, the disagreement rate is over this sample, not a random sample of all traces.",
             "", "For each trace, mark **agree** (the filter's decision is right) or **disagree**, with a note. For a "
             "kept trace, disagree means it should not be used for training; for a rejected one, that it should "
             f"have been kept. Tool outputs are cut at {OUTPUT_CHARS} characters; the full text is in "
             "`traces/<teacher>/traces.jsonl`.", ""]
    for v in sample:
        task, trace = tasks[v["id"]], traces[(v["id"], v["teacher"])]
        status = "kept" + (", edited" if v["edited"] else "") if v["kept"] else \
            ("rejected: " + "; ".join(v["reasons"]))
        lines += [f"## {v['id']} · {v['teacher']} · {task['type']} · {status}", "",
                  f"**Question:** {task['question']}", "", f"**Reference:** {task['reference']}", "",
                  f"**Required numbers:** {task['required_numbers']} · **requires caveat:** {task['requires_caveat']}",
                  ""]
        for i, turn in enumerate(trace["turns"], 1):
            for call in turn["tool_calls"]:
                args = ", ".join(f"{k}={val!r}" for k, val in call["args"].items())
                lines += [f"**Turn {i} call** `{call['name']}({args})`" + (" (error)" if call["is_error"] else ""),
                          "", "```text", _cut(call["output"]), "```", ""]
        lines += ["**Answer:**", "", "```text", trace["answer"], "```", ""]
        if v["edited"]:
            lines += ["**Answer after the edit:**", "", "```text", code_checks(task, trace)["answer"], "```", ""]
        if (label := judged.get((v["id"], v["teacher"]))):
            lines += [f"**Judge:** {label['correctness']}, caveat stated {label['caveat_stated']}: "
                      f"{label.get('explanation', '')}", ""]
        lines += ["**Verdict:** ", "", "**Note:** ", ""]
    return "\n".join(lines)


def _set_args(args):
    """Arguments without explicit nulls (gpt-oss writes `region_id: null`). Every such argument defaults to null, so
    the call is the same; Gemma's template would render the null as a bare word the parser reads back as text."""
    return {k: v for k, v in args.items() if v is not None} if isinstance(args, dict) else args


def training_example(task: dict, trace: dict, tool_schemas: list[dict]) -> dict:
    """One conversation in the Hugging Face chat format: assistant turns with tool calls, tool results, and the final
    answer. Reasoning text is left out; the edited answer replaces the original."""
    messages = [{"role": "system", "content": loop.SYSTEM_PROMPT}, {"role": "user", "content": task["question"]}]
    for i, turn in enumerate(trace["turns"]):
        last = i == len(trace["turns"]) - 1
        if last and not turn["tool_calls"]:
            messages.append({"role": "assistant", "content": trace["answer"]})
            break
        messages.append({"role": "assistant", "content": turn["content"],
                         "tool_calls": [{"type": "function", "function": {"name": c["name"], "arguments": _set_args(c["args"])}}
                                        for c in turn["tool_calls"]]})
        for call in turn["tool_calls"]:
            messages.append({"role": "tool", "name": call["name"], "content": call["output"]})
    return {"id": task["id"], "teacher": trace["teacher"], "edited": trace["edited"], "messages": messages,
            "tools": [{"type": "function", "function": schema} for schema in tool_schemas]}


async def _schemas() -> list[dict]:
    async with Client(server.mcp) as client:
        return (await loop.Toolbox.create(client)).schemas


def write_training() -> int:
    tasks = {row["id"]: row for row in questions()}
    schemas = asyncio.run(_schemas())
    rows = [training_example(tasks[t["id"]], t, schemas) for t in _read(OUT / "kept.jsonl")]
    (OUT / "train.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    return len(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--teacher", required=True, choices=sorted(SYSTEMS))
    run.add_argument("--limit", type=int, help="first N questions only (for a check)")
    commands.add_parser("judge")
    commands.add_parser("select")
    commands.add_parser("review")
    args = parser.parse_args(argv)
    if args.command == "run":
        rows = questions()
        asyncio.run(_run(args.teacher, rows[:args.limit] if args.limit else rows))
    elif args.command == "judge":
        judge()
    elif args.command == "review":
        path = OUT / "traces-review.md"
        path.write_text(trace_review_sheet(trace_review_sample()))
        print(f"wrote {path}")
    else:
        print(json.dumps(select(), indent=1))
        print(f"{write_training()} training conversations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
