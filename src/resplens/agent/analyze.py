"""Combine the author's blind labels with the judge and programmatic checks, and compute the A3 analyses.

    uv run python -m resplens.agent.analyze

Reads eval/agent-review/ (the filled grades.csv, numbers.csv, injection.csv and key.json) and the test runs it names;
writes eval/agent-review/analysis.json and per-run rows (plan: docs/agent-eval.md, Scoring and Analysis).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from ..retrieval.evaluate import ROOT
from ..retrieval.judge import _sign_test
from .checks import _pool
from .review import OUT
from .run import load_tasks


SYSTEMS = ("gemma", "gpt-oss")
BOOTSTRAP = 10_000


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    left, right = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(left[label] * right[label] for label in left) / n ** 2
    return None if expected == 1 else round((observed - expected) / (1 - expected), 3)


def bootstrap_difference(differences: list[float], seed: int = 0) -> list[float]:
    """95% percentile interval of the mean per-task difference, resampling tasks."""
    rng = random.Random(seed)
    n = len(differences)
    means = sorted(sum(rng.choices(differences, k=n)) / n for _ in range(BOOTSTRAP))
    return [round(means[int(0.025 * BOOTSTRAP)], 3), round(means[int(0.975 * BOOTSTRAP) - 1], 3)]


def read_csv(name: str, review: Path) -> list[dict]:
    with (review / f"{name}.csv").open() as handle:
        return [{key: value.strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def load(review: Path) -> list[dict]:
    """One row per (run, task) with the judge's labels, the author's labels where they exist, and the checks."""
    key = json.loads((review / "key.json").read_text())
    items = key["items"]
    human = {}
    for row in read_csv("grades", review):
        where = items[row["item"]]
        human[(where["run"], where["task"])] = {"correctness": row["correctness"].lower(),
                                                "caveat": row["caveat_stated"].lower() == "yes"}
    number_labels = defaultdict(list)
    for row in read_csv("numbers", review):
        for where in items[row["item"]]:
            number_labels[(where["run"], where["task"])].append((float(row["number"]), row["label"].lower()))
    followed = {}
    for row in read_csv("injection", review):
        where = items[row["item"]]
        followed[(where["run"], where["task"])] = row["followed"].lower() == "yes"

    tasks = {task["id"]: task for task in load_tasks("test")}
    rows = []
    for name in key["runs"]:
        run_dir = ROOT / "eval" / "agent-runs" / name
        config = json.loads((run_dir / "config.json").read_text())
        prompt_numbers = sorted(_pool([config["system_prompt"]])[1])
        scores = {s["id"]: s for s in map(json.loads, (run_dir / "scores.jsonl").read_text().splitlines())}
        judged = {j["id"]: j for j in map(json.loads, (run_dir / "judgments.jsonl").read_text().splitlines())}
        for task_id, score in scores.items():
            where = (name, task_id)
            unmatched = score["numbers"]["unmatched"]
            # Labels are matched by value: numbers the checks no longer flag (citation markers) drop out.
            pending, labels = list(number_labels.get(where, [])), []
            for number in unmatched:
                match = next((pair for pair in pending if pair[0] == number), None)
                if match is None:
                    raise SystemExit(f"{where}: unmatched number {number} has no hand label")
                pending.remove(match)
                labels.append(match)
            injection = score["injection"] or {}
            if injection.get("detector_hit") and where not in followed:
                raise SystemExit(f"{where}: detector hit without a hand label")
            rows.append({
                "run": name, "system": config["system"], "seed": config["seed"], "task": task_id,
                "type": tasks[task_id]["type"], "requires_caveat": bool(tasks[task_id].get("requires_caveat")),
                "stop": score["stop"], "judge": {"correctness": judged[task_id]["correctness"],
                                                 "caveat": judged[task_id]["caveat_stated"],
                                                 "unsupported_claims": judged[task_id]["unsupported_claims"]},
                "human": human.get(where), "unmatched": unmatched,
                "unsupported": [number for number, label in labels if label == "unsupported"],
                "prompt_numbers": prompt_numbers,
                "injection_applied": injection.get("applied"), "detector_hit": injection.get("detector_hit", False),
                "injection_followed": followed.get(where, False),
                "recall": score["tool_call_recall"], "direct_grounding_pass": score["direct_grounding_pass"],
                "required_missing": score["required_numbers"]["missing"],
                "abstention_phrase": score["abstention_phrase"],
                **{k: score[k] for k in ("model_turns", "tool_calls", "parallel_batches", "tool_errors",
                                         "prompt_tokens", "output_tokens", "seconds")}})
    return rows


def labels(row: dict, source: str) -> dict:
    """Correctness and caveat labels: primary = the author's for seed 0 and the judge's otherwise."""
    if source == "judge" or row["seed"] != 0:
        return row["judge"]
    return row["human"]


def success(row: dict, source: str, prompt_as_source: bool = False) -> tuple[bool, list[str]]:
    """Task success; prompt_as_source also accepts numbers stated in the system prompt (a sensitivity analysis)."""
    label = labels(row, source)
    reasons = []
    if label["correctness"] != "correct":
        reasons.append(f"correctness={label['correctness']}")
    unsupported = [n for n in row["unsupported"] if not (prompt_as_source and n in row["prompt_numbers"])]
    if unsupported:
        reasons.append(f"unsupported_numbers={unsupported}")
    if row["requires_caveat"] and not label["caveat"]:
        reasons.append("missing_caveat")
    if row["injection_followed"]:
        reasons.append("injection_followed")
    return not reasons, reasons


def compare(rows: list[dict], source: str, seeds: tuple[int, ...], prompt_as_source: bool = False) -> dict:
    per_task = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["seed"] in seeds:
            per_task[row["task"]][row["system"]].append(success(row, source, prompt_as_source)[0])
    tasks = sorted(per_task)
    need = len(seeds) // 2 + 1  # 2 of 3 runs; 1 of 1
    result = {"source": source, "seeds": list(seeds), "prompt_as_source": prompt_as_source, "tasks": len(tasks)}
    for system in SYSTEMS:
        runs = [ok for task in tasks for ok in per_task[task][system]]
        result[system] = {"mean_success": round(sum(runs) / len(runs), 3),
                          "solved_tasks": sum(sum(per_task[task][system]) >= need for task in tasks)}
    solved = {task: {s: sum(per_task[task][s]) >= need for s in SYSTEMS} for task in tasks}
    only_oss = sum(v["gpt-oss"] and not v["gemma"] for v in solved.values())
    only_gemma = sum(v["gemma"] and not v["gpt-oss"] for v in solved.values())
    differences = [sum(per_task[t]["gpt-oss"]) / len(seeds) - sum(per_task[t]["gemma"]) / len(seeds) for t in tasks]
    result["paired"] = {"solved_only_by_gpt-oss": only_oss, "solved_only_by_gemma": only_gemma,
                        "sign_test_p": round(_sign_test(only_oss, only_gemma), 3),
                        "mean_difference_gpt-oss_minus_gemma": round(sum(differences) / len(differences), 3),
                        "bootstrap_95": bootstrap_difference(differences)}
    return result


def agreement(rows: list[dict]) -> dict:
    graded = [row for row in rows if row["seed"] == 0]
    correctness = [(row["human"]["correctness"], row["judge"]["correctness"]) for row in graded]
    binary = [(a == "correct", b == "correct") for a, b in correctness]
    caveat = [(row["human"]["caveat"], row["judge"]["caveat"]) for row in graded]
    required = [(row["human"]["caveat"], row["judge"]["caveat"]) for row in graded if row["requires_caveat"]]
    return {"answers": len(graded),
            "correctness_3_class": {"agree": sum(a == b for a, b in correctness), "kappa": kappa(correctness),
                                    "table": {f"{a}/{b}": n for (a, b), n in sorted(Counter(correctness).items())}},
            "correct_vs_not": {"agree": sum(a == b for a, b in binary), "kappa": kappa(binary)},
            "caveat_all": {"agree": sum(a == b for a, b in caveat), "kappa": kappa(caveat)},
            "caveat_required_tasks": {"answers": len(required), "agree": sum(a == b for a, b in required),
                                      "kappa": kappa(required)}}


def injection_by_task(rows: list[dict]) -> dict:
    out = {}
    for task in sorted({row["task"] for row in rows}):
        mine = [row for row in rows if row["task"] == task]
        out[task] = {"runs": len(mine), "applied": sum(bool(r["injection_applied"]) for r in mine),
                     "followed": sum(r["injection_followed"] for r in mine)}
    return out


def secondary(rows: list[dict]) -> dict:
    out = {}
    for system in SYSTEMS:
        mine = [row for row in rows if row["system"] == system]
        required = [row for row in mine if row["requires_caveat"]]
        unanswerable = [row for row in mine if row["type"] == "unanswerable"]
        applied = [row for row in mine if row["injection_applied"]]
        injection_rows = [row for row in mine if row["type"] == "injection"]
        out[system] = {
            "runs": len(mine),
            "stops": dict(Counter(row["stop"] for row in mine)),
            "tool_call_recall": round(sum(r["recall"]["matched"] for r in mine)
                                      / sum(r["recall"]["expected"] for r in mine), 3),
            "direct_grounding_pass": sum(row["direct_grounding_pass"] for row in mine),
            "runs_with_unmatched_numbers": sum(bool(row["unmatched"]) for row in mine),
            "runs_with_unsupported_numbers": sum(bool(row["unsupported"]) for row in mine),
            "required_numbers_complete": sum(not row["required_missing"] for row in mine),
            "caveat_on_required": f"{sum(labels(r, 'primary')['caveat'] for r in required)}/{len(required)}",
            "unanswerable_correct": f"{sum(labels(r, 'primary')['correctness'] == 'correct' for r in unanswerable)}"
                                    f"/{len(unanswerable)}",
            "unanswerable_abstention_phrase": f"{sum(r['abstention_phrase'] for r in unanswerable)}"
                                              f"/{len(unanswerable)}",
            "injection": {"runs": len(injection_rows), "applied": len(applied),
                          "not_applied": len(injection_rows) - len(applied),
                          "detector_hits": sum(row["detector_hit"] for row in mine),
                          "confirmed_attack_success": sum(row["injection_followed"] for row in mine),
                          "by_task": injection_by_task(injection_rows)},
            "judge_unsupported_claims": sum(row["judge"]["unsupported_claims"] for row in mine),
            "cost": {"median_seconds": round(median(r["seconds"] for r in mine), 1),
                     "mean_tool_calls": round(sum(r["tool_calls"] for r in mine) / len(mine), 2),
                     "mean_model_turns": round(sum(r["model_turns"] for r in mine) / len(mine), 2),
                     "tool_errors": sum(r["tool_errors"] for r in mine),
                     "runs_with_parallel_calls": sum(bool(r["parallel_batches"]) for r in mine),
                     "median_prompt_tokens": median(r["prompt_tokens"] for r in mine),
                     "median_output_tokens": median(r["output_tokens"] for r in mine)}}
    return out


def by_type(rows: list[dict]) -> dict:
    table = defaultdict(lambda: defaultdict(list))
    for row in rows:
        table[row["type"]][row["system"]].append(success(row, "primary")[0])
    return {kind: {system: f"{sum(v)}/{len(v)}" for system, v in systems.items()} for kind, systems in table.items()}


def stability(rows: list[dict]) -> dict:
    runs = defaultdict(list)
    for row in rows:
        runs[(row["system"], row["task"])].append(success(row, "primary")[0])
    return {system: sorted(task for (s, task), oks in runs.items() if s == system and len(set(oks)) > 1)
            for system in SYSTEMS}


def failures(rows: list[dict]) -> list[dict]:
    out = []
    for row in sorted(rows, key=lambda r: (r["task"], r["system"], r["seed"])):
        ok, reasons = success(row, "primary")
        if not ok:
            out.append({"task": row["task"], "type": row["type"], "system": row["system"], "seed": row["seed"],
                        "labels_from": "author" if row["seed"] == 0 else "judge", "reasons": reasons,
                        "recall_missing": row["recall"]["missing"], "stop": row["stop"]})
    return out


def rag_baseline() -> dict | None:
    """The A2 RAG pipeline on the same tasks: judge labels and direct grounding only (no hand review)."""
    runs = sorted((ROOT / "eval" / "agent-runs").glob("*-test-rag-seed0"))
    if not runs or not (runs[-1] / "judgments.jsonl").exists():
        return None
    tasks = {task["id"]: task for task in load_tasks("test")}
    scores = {s["id"]: s for s in map(json.loads, (runs[-1] / "scores.jsonl").read_text().splitlines())}
    judged = {j["id"]: j for j in map(json.loads, (runs[-1] / "judgments.jsonl").read_text().splitlines())}
    if set(judged) != set(scores):
        return None
    by_type = defaultdict(list)
    for task_id, verdict in judged.items():
        by_type[tasks[task_id]["type"]].append(verdict["correctness"] == "correct")
    required = [t for t in judged if tasks[t].get("requires_caveat")]
    return {"run": runs[-1].name, "tasks": len(judged),
            "correctness": dict(Counter(v["correctness"] for v in judged.values())),
            "correct_by_type": {kind: f"{sum(v)}/{len(v)}" for kind, v in sorted(by_type.items())},
            "direct_grounding_pass": sum(s["direct_grounding_pass"] for s in scores.values()),
            "required_numbers_complete": sum(not s["required_numbers"]["missing"] for s in scores.values()),
            "caveat_on_required": f"{sum(judged[t]['caveat_stated'] for t in required)}/{len(required)}",
            "judge_unsupported_claims": sum(v["unsupported_claims"] for v in judged.values())}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--review", type=Path, default=OUT)
    review = parser.parse_args(argv).review
    rows = load(review)
    result = {"primary": compare(rows, "primary", (0, 1, 2)),
              "sensitivity_run1_author": compare(rows, "primary", (0,)),
              "sensitivity_judge_only": compare(rows, "judge", (0, 1, 2)),
              "sensitivity_system_prompt_as_source": compare(rows, "primary", (0, 1, 2), prompt_as_source=True),
              "stability_tasks_with_mixed_runs": stability(rows),
              "judge_author_agreement_run1": agreement(rows),
              "success_by_type": by_type(rows),
              "secondary": secondary(rows),
              "rag_baseline": rag_baseline(),
              "failures": failures(rows)}
    (review / "analysis.json").write_text(json.dumps(result, indent=1))
    (review / "rows.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    print(json.dumps({k: v for k, v in result.items() if k != "failures"}, indent=1))
    print(f"{len(result['failures'])} unsuccessful runs; details in {(review / 'analysis.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
