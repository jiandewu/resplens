"""Build the static replay of the A3 test runs (design: docs/deploy.md).

    uv run python -m resplens.app.replay --out site

Reads only files in the repository: eval/tasks.jsonl, the test runs in eval/agent-runs/, and eval/agent-review/
(rows.jsonl, analysis.json). Writes the page, its script and stylesheet, and data.json. Labels and task success
come from the evaluation code; the number check is recomputed and must match the stored one.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from ..agent.analyze import success
from ..agent.checks import grounding
from ..agent.run import load_tasks
from ..retrieval.evaluate import ROOT

STATIC = Path(__file__).parent / "static"
RUNS = ROOT / "eval" / "agent-runs"
REVIEW = ROOT / "eval" / "agent-review"
AGENT_SYSTEMS = ["gemma", "gpt-oss"]
SOURCE = "primary"  # author's labels for seed 0, the judge's for seeds 1-2, as in docs/agent-results.md
RESULTS_URL = "https://github.com/jiandewu/resplens/blob/main/docs/agent-results.md"
RAG_CORRECTED = ["b01", "b03", "b06", "b10"]  # docs/agent-results.md, "RAG-only baseline"


class ReplayError(RuntimeError):
    pass


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def _turns(trace: dict) -> list[dict]:
    return [{"content": turn.get("content", ""), "thinking": turn.get("thinking", ""),
             "tool_calls": [{"name": c["name"], "args": c["args"], "output": c["output"], "is_error": c["is_error"]}
                            for c in turn.get("tool_calls", [])]}
            for turn in trace["turns"]]


def _outputs(trace: dict) -> list[str]:
    return [c["output"] for turn in trace["turns"] for c in turn.get("tool_calls", [])]


def _numbers(trace: dict, question: str, stored_unmatched: list) -> dict:
    """The evaluation's number check, recomputed; it must give the stored result."""
    check = grounding(trace["answer"], question, _outputs(trace))
    if check["unmatched"] != stored_unmatched:
        raise ReplayError(f"{trace['id']}: recomputed unmatched {check['unmatched']} != stored {stored_unmatched}")
    return check


def agent_run(row: dict, trace: dict, question: str) -> dict:
    ok, reasons = success(row, SOURCE)
    label = row["human"] if row["seed"] == 0 else row["judge"]
    check = _numbers(trace, question, row["unmatched"])
    return {"seed": row["seed"], "label_source": "author" if row["seed"] == 0 else "judge",
            "correctness": label["correctness"], "caveat": label["caveat"], "success": ok, "reasons": reasons,
            "direct": check["direct"], "unsupported": row["unsupported"],
            "checked_by_hand": [n for n in row["unmatched"] if n not in row["unsupported"]],
            "injection_seen": bool(row["injection_applied"]), "injection_followed": row["injection_followed"],
            "stop": trace["stop"], "answer": trace["answer"], "turns": _turns(trace),
            "seconds": trace["seconds"], "prompt_tokens": trace["prompt_tokens"],
            "output_tokens": trace["output_tokens"]}


def rag_run(trace: dict, judged: dict, task: dict) -> dict:
    corrected = judged["abstained"] and judged["correctness"] == "correct" and task["type"] != "unanswerable"
    correctness = "incorrect" if corrected else judged["correctness"]
    check = grounding(trace["answer"], task["question"], _outputs(trace))
    return {"seed": 0, "label_source": "judge, corrected by hand" if corrected else "judge",
            "correctness": correctness, "caveat": judged["caveat_stated"], "success": None,
            "reasons": ["refusal accepted by the judge, counted as not correct"] if corrected else [],
            "direct": check["direct"], "unsupported": [], "checked_by_hand": [],
            "unmatched": check["unmatched"], "injection_seen": False, "injection_followed": False,
            "stop": trace["stop"], "answer": trace["answer"], "turns": _turns(trace),
            "seconds": trace["seconds"], "prompt_tokens": trace["prompt_tokens"],
            "output_tokens": trace["output_tokens"]}


def build() -> dict:
    tasks = {task["id"]: task for task in load_tasks("test")}
    rows = _jsonl(REVIEW / "rows.jsonl")
    analysis = json.loads((REVIEW / "analysis.json").read_text())
    traces = {row["run"]: {t["id"]: t for t in _jsonl(RUNS / row["run"] / "traces.jsonl")}
              for row in rows}
    models = {}
    for run in traces:
        config = json.loads((RUNS / run / "config.json").read_text())
        models[config["system"]] = config["model"]
    runs = {task_id: {system: [] for system in [*AGENT_SYSTEMS, "rag"]} for task_id in tasks}
    for row in sorted(rows, key=lambda r: (r["task"], r["system"], r["seed"])):
        trace = traces[row["run"]][row["task"]]
        runs[row["task"]][row["system"]].append(agent_run(row, trace, tasks[row["task"]]["question"]))

    rag_dir = sorted(RUNS.glob("*-test-rag-seed0"))[-1]
    judged = {j["id"]: j for j in _jsonl(rag_dir / "judgments.jsonl")}
    for trace in _jsonl(rag_dir / "traces.jsonl"):
        runs[trace["id"]]["rag"].append(rag_run(trace, judged[trace["id"]], tasks[trace["id"]]))
    corrected = sorted(t for t, r in runs.items() if r["rag"] and "corrected" in r["rag"][0]["label_source"])
    rag_correct = sum(r["rag"][0]["correctness"] == "correct" for r in runs.values() if r["rag"])
    if corrected != RAG_CORRECTED or rag_correct != 7:
        raise ReplayError(f"RAG corrections {corrected}, {rag_correct} correct; docs/agent-results.md says "
                          f"{RAG_CORRECTED} and 7")
    rag_config = json.loads((rag_dir / "config.json").read_text())
    models["rag"] = rag_config.get("model", "")

    for task_id, by_system in runs.items():
        for system in AGENT_SYSTEMS:
            if [r["seed"] for r in by_system[system]] != [0, 1, 2]:
                raise ReplayError(f"{task_id} {system}: seeds {[r['seed'] for r in by_system[system]]}")

    primary = analysis["primary"]
    return {"results_url": RESULTS_URL, "models": models,
            "summary": {"tasks": primary["tasks"],
                        "solved": {s: primary[s]["solved_tasks"] for s in AGENT_SYSTEMS},
                        "mean_success": {s: primary[s]["mean_success"] for s in AGENT_SYSTEMS},
                        "sign_test_p": primary["paired"]["sign_test_p"],
                        "difference_ci95": primary["paired"]["bootstrap_95"],
                        "rag_correct": rag_correct},
            "tasks": [{"id": t["id"], "type": t["type"], "question": t["question"], "reference": t["reference"],
                       "requires_caveat": t["requires_caveat"],
                       "injection": ({"vector": t["injection"]["vector"], "target": t["injection"]["target"],
                                      "payload": t["injection"]["payload"],
                                      "detector": t["injection"]["detector"]} if t.get("injection") else None),
                       "runs": runs[t["id"]]}
                      for t in sorted(tasks.values(), key=lambda t: t["id"])]}


def write(out: Path) -> Path:
    data = build()
    out.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "replay.js", "replay.css"):
        shutil.copyfile(STATIC / name, out / name)
    (out / "data.json").write_text(json.dumps(data, separators=(",", ":")))
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / "site")
    out = write(parser.parse_args(argv).out)
    print(f"replay written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
