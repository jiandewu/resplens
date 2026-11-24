"""Counterfactual tool outputs: do answer numbers follow the tools or come back from memory?
Plan: docs/counterfactual-eval.md.

    uv run python -m resplens.agent.counterfactual eligible                 # every candidate question, once
    uv run python -m resplens.agent.counterfactual sample --split dev
    uv run python -m resplens.agent.counterfactual run --split dev --system b2-ft --seed 0 --condition perturbed \
        --url http://127.0.0.1:8106 --info '{...}'                                    # vLLM must be serving
    uv run python -m resplens.agent.counterfactual score --split dev
    uv run python -m resplens.agent.counterfactual analyze --split dev

Questions come from the B2 question set: arm M from the training questions whose kept trace was trained on, arm C
from the validation questions. Every value of a scaled measure in get_series, get_as_of and get_revisions is
multiplied by one factor per question; everything else is left as published.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import math
import random
from collections import Counter, defaultdict
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any

from ..data import DATA_TAG
from ..finetune.questions import OUT as FINETUNE, _read
from ..finetune.traces import DROPPED_TEMPLATES
from ..retrieval.evaluate import ROOT, _git_commit
from ..retrieval.judge import _sign_test
from . import checks, loop
from .analyze import bootstrap_difference
from .run import RUN_INPUTS, SYSTEMS as ALL_SYSTEMS

OUT = ROOT / "eval" / "counterfactual"
TYPES = ("trend_reliability", "lookup", "revision", "mixed")
# Numeric measures whose values are scaled. hospital_reporting_count is left alone: it is compared with the state
# threshold, and the reliability flags depend on it.
SCALED_MEASURES = ("hospital_admission_count", "ed_visit_percent", "ed_visit_percent_smoothed",
                   "wastewater_activity_level")
VALUE_KEYS = ("value", "first_value", "latest_value")
# The author's decisions 2026-11-23 (the draft's proposals).
FACTORS = (0.7, 0.8, 1.25, 1.4)
MIN_VALUE = 5
SIZES = {"dev": {"M": 10, "C": 5}, "test": {"M": 60, "C": 30}}
FACTOR_SEED = 20261123  # one factor per question, drawn before eligibility
# Dev seed 20261124: the first dev draw (20261123) was made before eligibility under the draft rule and replaced
# (R1, the author's decision 2026-11-23). Test seed set at freezing (2026-11-24).
SAMPLE_SEEDS = {"dev": 20261124, "test": 20261125}
SYSTEMS = ("b2-base", "b2-ft")
CONDITIONS = ("original", "perturbed")
SEEDS = (0, 1, 2)
RUN_FILES = [*RUN_INPUTS, "eval/finetune/questions.jsonl", "eval/finetune/kept.jsonl",
             "eval/counterfactual/eligibility.jsonl", "eval/counterfactual/dev-sample.jsonl",
             "eval/counterfactual/test-sample.jsonl"]


# --- questions -------------------------------------------------------------------------------------------------

def candidates(arm: str) -> list[dict]:
    rows = _read(FINETUNE / "questions.jsonl")
    if arm == "M":
        kept = {row["id"] for row in _read(FINETUNE / "kept.jsonl")}
        rows = [row for row in rows if row["split"] == "train" and row["id"] in kept]
    else:
        rows = [row for row in rows if row["split"] == "validation" and row["origin"] not in DROPPED_TEMPLATES]
    return sorted((row for row in rows if row["type"] in TYPES and row["required_numbers"]), key=lambda r: r["id"])


def stratified(rows: list[dict], n: int, rng: random.Random) -> list[dict]:
    """n rows, allocated to types in proportion to their counts (largest remainder), drawn at random in each type."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["type"]].append(row)
    shares = {t: n * len(groups[t]) / len(rows) for t in sorted(groups)}
    counts = {t: int(share) for t, share in shares.items()}
    for t in sorted(shares, key=lambda t: (counts[t] - shares[t], t))[:n - sum(counts.values())]:
        counts[t] += 1
    picked = []
    for t in sorted(groups):
        picked += rng.sample(groups[t], counts[t])
    return picked


def factor(question_id: str) -> float:
    return random.Random(f"{FACTOR_SEED}:{question_id}").choice(FACTORS)


def sample(split: str, seed: int | None = None) -> list[dict]:
    """A stratified draw from the eligible questions of each arm, disjoint from the other split's sample."""
    seed = SAMPLE_SEEDS.get(split) if seed is None else seed
    if seed is None:
        raise SystemExit(f"no sample seed for {split}: pass --seed (fixed at freezing)")
    taken = {row["id"] for other in SIZES if other != split and (OUT / f"{other}-sample.jsonl").exists()
             for row in _read(OUT / f"{other}-sample.jsonl")}
    rows = [row for row in _read(OUT / "eligibility.jsonl") if row["eligible"] and row["id"] not in taken]
    rng = random.Random(seed)
    out = []
    for arm in ("M", "C"):
        out += [{**row, "seed": seed} for row in stratified([r for r in rows if r["arm"] == arm],
                                                            SIZES[split][arm], rng)]
    return out


# --- perturbation ----------------------------------------------------------------------------------------------

def _number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def scale_value(value, factor: float):
    if isinstance(value, int):
        return int(math.floor(value * factor + 0.5))
    fraction = repr(float(value)).partition(".")[2]
    places = max(1, len(fraction.rstrip("0"))) if "e" not in fraction else 6
    return round(value * factor, places)


def _walk(node, visit):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in VALUE_KEYS and _number(value):
                node[key] = visit(value)
            else:
                _walk(value, visit)
    elif isinstance(node, list):
        for item in node:
            _walk(item, visit)


def scale(output: Any, factor: float) -> Any:
    """A copy of a tool output with every value of a scaled measure multiplied by factor; anything else unchanged."""
    if not isinstance(output, dict) or output.get("measure") not in SCALED_MEASURES:
        return output
    out = copy.deepcopy(output)
    _walk(out, lambda value: scale_value(value, factor))
    first, last = out.get("first_value"), out.get("latest_value")
    if out.get("percent_change_first_to_latest") is not None and _number(first) and _number(last) and first:
        out["percent_change_first_to_latest"] = round((last - first) / abs(first) * 100, 1)  # as tools.get_revisions
    return out


def scaled_values(output: Any) -> list[float]:
    values = []
    if isinstance(output, dict) and output.get("measure") in SCALED_MEASURES:
        _walk(copy.deepcopy(output), lambda value: values.append(float(value)) or value)
    return values


class Perturbation:
    """The toolbox hook: keeps every original data-tool output and returns it scaled (factor None: unchanged)."""

    def __init__(self, factor: float | None):
        self.factor, self.originals = factor, []

    def __call__(self, name: str, output: Any) -> Any:
        self.originals.append(json.dumps(output, indent=2))
        return output if self.factor is None else scale(output, self.factor)


def _numbers(texts: list[str]) -> set[float]:
    return checks._pool(texts)[1]


def eligibility(question: dict, factor: float, outputs: list[dict]) -> dict:
    """Whether every required number is a scaled value of at least MIN_VALUE that scaling changes. outputs are the
    expected calls' data-tool outputs, unperturbed. A value that also appears elsewhere in a run's outputs is
    handled per run by the scorer (R1, the author's decision 2026-11-23), not here."""
    mapping = defaultdict(set)
    for output in outputs:
        for original, perturbed in zip(scaled_values(output), scaled_values(scale(output, factor))):
            mapping[original].add(perturbed)
    reasons, numbers = [], []
    for required in question["required_numbers"]:
        original = float(required)
        if original not in mapping:
            reasons.append(f"{required}: not a scaled value")
            continue
        if len(mapping[original]) > 1:
            reasons.append(f"{required}: scales to more than one value")
            continue
        perturbed = next(iter(mapping[original]))
        if abs(original) < MIN_VALUE:
            reasons.append(f"{required}: below {MIN_VALUE}")
        elif perturbed == original:
            reasons.append(f"{required}: unchanged by scaling")
        numbers.append({"original": original, "perturbed": perturbed})
    return {"eligible": not reasons, "reasons": reasons, "numbers": numbers}


async def expected_outputs(client, question: dict) -> list[dict] | None:
    """The unperturbed outputs of a question's expected data-tool calls (search_docs is not scaled, so left out)."""
    outputs = []
    for call in question["expected_calls"]:
        if call["tool"] == "search_docs":
            continue
        result = await client.call_tool(call["tool"], call["args"])
        if result.is_error or result.structured_content is None:
            return None
        outputs.append(result.structured_content)
    return outputs


async def eligible() -> list[dict]:
    """Eligibility of every candidate question in both arms (model-independent, before any run)."""
    from mcp import Client

    from .. import server
    rows = []
    async with Client(server.mcp) as client:
        for arm in ("M", "C"):
            for question in candidates(arm):
                row = {"id": question["id"], "arm": arm, "type": question["type"], "origin": question["origin"],
                       "factor": factor(question["id"])}
                outputs = await expected_outputs(client, question)
                check = {"eligible": False, "reasons": ["an expected call failed"], "numbers": []} \
                    if outputs is None else eligibility(question, row["factor"], outputs)
                rows.append({**row, **check})
    return rows


# --- runs ------------------------------------------------------------------------------------------------------

def run_dir(split: str, system: str, seed: int, condition: str) -> Path:
    return OUT / "runs" / f"{split}-{system}-seed{seed}-{condition}"


async def run(split: str, system: str, seed: int, condition: str, url: str | None, info: dict) -> Path:
    from mcp import Client

    from .. import server
    questions = {row["id"]: row for row in _read(FINETUNE / "questions.jsonl")}
    rows = _read(OUT / f"{split}-sample.jsonl")
    spec = ALL_SYSTEMS[system]
    directory = run_dir(split, system, seed, condition)
    directory.mkdir(parents=True, exist_ok=True)
    out = directory / "traces.jsonl"
    done = {row["id"] for row in _read(out)} if out.exists() else set()
    chat = partial(loop.openai_chat, url=url)
    async with Client(server.mcp) as client:
        toolbox = await loop.Toolbox.create(client)
        config = directory / "config.json"
        if not config.exists():
            config.write_text(json.dumps({
                "split": split, "system": system, "model": spec["model"], "url": url or loop.OPENAI_URL, **info,
                "seed": seed, "condition": condition, "temperature": 0, "max_output": loop.MAX_OUTPUT,
                "max_turns": loop.MAX_TURNS, "max_tool_calls": loop.MAX_TOOL_CALLS,
                "system_prompt": loop.SYSTEM_PROMPT, "tools": toolbox.schemas, "data_release": DATA_TAG,
                "scaled_measures": SCALED_MEASURES, "item_ids": [row["id"] for row in rows],
                "git_commit": _git_commit(inputs=RUN_FILES), "started": datetime.now().isoformat(timespec="seconds")},
                indent=1))
        with out.open("a") as handle:
            for row in rows:
                if row["id"] in done:
                    continue
                question = questions[row["id"]]
                hook = Perturbation(row["factor"] if condition == "perturbed" else None)
                toolbox.perturb = hook
                try:
                    trace = (await loop.run_task({"id": row["id"], "question": question["question"]}, toolbox,
                                                 spec["model"], spec["think"], seed, chat_fn=chat)).to_dict()
                finally:
                    toolbox.perturb = None
                trace.update(arm=row["arm"], condition=condition, factor=hook.factor,
                             original_outputs=hook.originals)
                handle.write(json.dumps(trace) + "\n")
                handle.flush()
                print(f"{directory.name} {row['id']} {trace['stop']} calls={trace['tool_calls']} "
                      f"{trace['seconds']:.1f}s", flush=True)
    return directory


# --- scoring ---------------------------------------------------------------------------------------------------

def score_trace(question: dict, row: dict, trace: dict) -> dict:
    """Each required number: follows (the perturbed value is in the answer), reverts (the original value is in the
    answer and in none of this run's tool outputs, the question or the prompt), ambiguous (the original value is in
    the answer but also in this run's outputs), or neither. In original runs: present or absent."""
    answer = set(checks.answer_tokens(trace["answer"])[1])
    calls = [call for turn in trace["turns"] for call in turn["tool_calls"] if not call["is_error"]]
    texts = [question["question"], loop.SYSTEM_PROMPT]
    run_pool = _numbers(texts + [call["output"] for call in calls])
    others = [call["output"] for call in calls if call["name"] == "search_docs"]
    original_pool = _numbers(texts + others + trace["original_outputs"])
    perturbed = trace["condition"] == "perturbed"
    numbers = []
    for pair in row["numbers"]:
        original, new = pair["original"], pair["perturbed"]
        if not perturbed:
            status = "present" if original in answer else "absent"
            seen = original in run_pool
        elif original in answer and original not in run_pool:
            status = "reverts"
            seen = new in run_pool
        else:
            status = "follows" if new in answer else "ambiguous" if original in answer else "neither"
            seen = new in run_pool
        numbers.append({**pair, "status": status, "seen": seen})
    candidates = sorted(n for n in answer if n not in run_pool and n in original_pool) if perturbed else []
    return {"id": trace["id"], "arm": trace["arm"], "condition": trace["condition"], "stop": trace["stop"],
            "numbers": numbers, "reverts": any(n["status"] == "reverts" for n in numbers),
            "all_follow": all(n["status"] == "follows" for n in numbers),
            "all_present": all(n["status"] == "present" for n in numbers), "revert_candidates": candidates,
            "unmatched": checks.grounding(trace["answer"], question["question"],
                                          [loop.SYSTEM_PROMPT, *(call["output"] for call in calls)])["unmatched"]}


def score(split: str) -> list[Path]:
    questions = {row["id"]: row for row in _read(FINETUNE / "questions.jsonl")}
    rows = {row["id"]: row for row in _read(OUT / f"{split}-sample.jsonl")}
    scored = []
    for directory in sorted((OUT / "runs").glob(f"{split}-*")):
        if not (directory / "traces.jsonl").exists():
            continue
        with (directory / "scores.jsonl").open("w") as handle:
            for trace in _read(directory / "traces.jsonl"):
                handle.write(json.dumps(score_trace(questions[trace["id"]], rows[trace["id"]], trace)) + "\n")
        scored.append(directory)
    return scored


# --- analysis --------------------------------------------------------------------------------------------------

def _load(split: str) -> dict:
    """(system, condition) -> question id -> list of score rows over seeds."""
    out = defaultdict(lambda: defaultdict(list))
    for directory in sorted((OUT / "runs").glob(f"{split}-*")):
        if (directory / "scores.jsonl").exists():
            config = json.loads((directory / "config.json").read_text())
            for row in _read(directory / "scores.jsonl"):
                out[(config["system"], config["condition"])][row["id"]].append(row)
    return out


def _rate(runs: list[dict], key: str) -> float:
    return sum(run[key] for run in runs) / len(runs)


def compare(by_question: dict, ids: list[str], first: str, second: str) -> dict:
    """second against first on perturbed runs: question-level reverts (2 of 3) and the run-level revert rate."""
    a, b = by_question[(first, "perturbed")], by_question[(second, "perturbed")]
    ids = [i for i in ids if a.get(i) and b.get(i)]
    if not ids:
        return {"questions": 0}
    reverting = {s: {i for i in ids if sum(r["reverts"] for r in runs[i]) >= 2} for s, runs in ((first, a), (second, b))}
    only_second, only_first = len(reverting[second] - reverting[first]), len(reverting[first] - reverting[second])
    differences = [_rate(b[i], "reverts") - _rate(a[i], "reverts") for i in ids]
    return {"questions": len(ids), f"reverting_{first}": len(reverting[first]),
            f"reverting_{second}": len(reverting[second]), f"only_{second}": only_second, f"only_{first}": only_first,
            "sign_test_p": round(_sign_test(only_second, only_first), 4),
            f"run_revert_rate_{first}": round(sum(_rate(a[i], "reverts") for i in ids) / len(ids), 3),
            f"run_revert_rate_{second}": round(sum(_rate(b[i], "reverts") for i in ids) / len(ids), 3),
            "difference": round(sum(differences) / len(ids), 3), "difference_ci95": bootstrap_difference(differences)}


def describe(by_question: dict, ids: list[str], system: str) -> dict:
    perturbed = [r for i in ids for r in by_question[(system, "perturbed")].get(i, [])]
    original = [r for i in ids for r in by_question[(system, "original")].get(i, [])]
    statuses = Counter(n["status"] for r in perturbed for n in r["numbers"])
    return {"perturbed_runs": len(perturbed), "runs_reverting": sum(r["reverts"] for r in perturbed),
            "runs_all_follow": sum(r["all_follow"] for r in perturbed), "number_status": dict(sorted(statuses.items())),
            "runs_with_revert_candidates": sum(bool(r["revert_candidates"]) for r in perturbed),
            "original_runs": len(original), "original_all_present": sum(r["all_present"] for r in original),
            "stops": dict(Counter(r["stop"] for r in perturbed + original))}


def analyze(split: str) -> dict:
    rows = _read(OUT / f"{split}-sample.jsonl")
    by_question = _load(split)
    result = {"split": split, "questions": dict(Counter(row["arm"] for row in rows))}
    for arm in ("M", "C"):
        ids = [row["id"] for row in rows if row["arm"] == arm]
        result[arm] = {"b2-ft_vs_b2-base": compare(by_question, ids, "b2-base", "b2-ft"),
                       **{system: describe(by_question, ids, system) for system in SYSTEMS}}
    (OUT / f"{split}-analysis.json").write_text(json.dumps(result, indent=1))
    return result


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("eligible")
    for name in ("sample", "run", "score", "analyze"):
        command = commands.add_parser(name)
        command.add_argument("--split", required=True, choices=list(SIZES))
        if name == "sample":
            command.add_argument("--seed", type=int)
        if name == "run":
            command.add_argument("--system", required=True, choices=SYSTEMS)
            command.add_argument("--seed", type=int, required=True, choices=SEEDS)
            command.add_argument("--condition", required=True, choices=CONDITIONS)
            command.add_argument("--url")
            command.add_argument("--info", default="{}", help="what is served, as JSON (recorded in config.json)")
    args = parser.parse_args(argv)
    if args.command == "sample":
        path = OUT / f"{args.split}-sample.jsonl"
        if path.exists():
            raise SystemExit(f"{path} exists; the sample is drawn once")
        rows = sample(args.split, args.seed)
        _write(path, rows)
        print(f"{path}: {dict(Counter((r['arm'], r['type']) for r in rows))}")
    elif args.command == "eligible":
        rows = asyncio.run(eligible())
        _write(OUT / "eligibility.jsonl", rows)
        print(dict(Counter((row["arm"], row["type"], row["eligible"]) for row in rows)))
    elif args.command == "run":
        asyncio.run(run(args.split, args.system, args.seed, args.condition, args.url, json.loads(args.info)))
    elif args.command == "score":
        for directory in score(args.split):
            print(directory.name)
    else:
        print(json.dumps(analyze(args.split), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
