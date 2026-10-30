"""Grade agent answers with the A2 judge and an extended rubric (plan: docs/agent-eval.md).

    uv run python -m resplens.agent.judge eval/agent-runs/<run>
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

from ..retrieval.dense import CPU_THREADS, OLLAMA_URL
from ..retrieval.evaluate import _git_commit
from ..retrieval.judge import JUDGE, LABELS, JudgeFailed
from .run import RUN_INPUTS, load_tasks, model_info


# A2 used 8192; on A3 dev the judge ran past it on 4 of about 60 answers (docs/agent-eval.md, 2026-10-30).
MAX_JUDGE_TOKENS = 16_384

JUDGE_PROMPT = """You grade an answer to a question about US respiratory surveillance data (weekly hospital \
admissions, emergency department visits, and wastewater) and its documentation.
You are given the question, a reference answer written by a human, evidence quotes from the documentation (if any), \
the outputs of the tools the answering system called (data tools and document search), and the answer to grade.

- correctness: judge the facts the question asks for; details in the reference answer beyond what the question asks \
are not required.
  "correct" if the answer gives every fact the question asks for, consistent with the reference answer (wording may \
differ; extra detail is fine if it does not contradict the reference, the evidence, or the tool outputs). If the \
reference says the data or documents do not answer the question, "correct" means the answer says so too, and does not \
supply an answer of its own.
  "partial" if it gives some of the asked-for facts correctly but misses others, or hedges where the reference is \
definite.
  "incorrect" if an asked-for fact is wrong or contradicts the reference, evidence, or tool outputs, if the answer \
gives none of the asked-for facts, or if it answers a question the reference says cannot be answered.
  A number that is derived from tool outputs (for example a difference) is fine when its inputs and calculation are \
correct.
- unsupported_claims: true if the answer states a specific fact (a number, date, rule, procedure, or definition) \
supported by none of the reference answer, the evidence, or the tool outputs. Restating the question or naming \
sources does not count.
- abstained: true if the answer says the data or documents do not answer the question.
- caveat_stated: true if the answer assesses the reliability of the data it reports: it mentions the reliability \
issues the reference mentions (for example anomalous weeks, reduced participation, undercounts), or, when the \
reference says no issues were flagged, it says so explicitly. False if it reports values without any statement \
about their reliability.

Return JSON only."""

SCHEMA = {"type": "object", "properties": {
    "correctness": {"type": "string", "enum": list(LABELS)},
    "unsupported_claims": {"type": "boolean"},
    "abstained": {"type": "boolean"},
    "caveat_stated": {"type": "boolean"},
    "explanation": {"type": "string"}},
    "required": ["correctness", "unsupported_claims", "abstained", "caveat_stated", "explanation"]}


def judge_input(task: dict, trace: dict) -> str:
    evidence = "\n".join(f"- ({item['doc']}) {item['quote']}" for item in task.get("evidence", [])) or "(none)"
    outputs = "\n\n".join(f"<tool_output name='{call['name']}' arguments='{json.dumps(call['args'])}'>\n"
                          f"{call['output']}\n</tool_output>"
                          for turn in trace["turns"] for call in turn["tool_calls"]) or "(no tool calls)"
    return (f"Question: {task['question']}\n\nReference answer: {task['reference']}\n\nEvidence:\n{evidence}\n\n"
            f"Tool outputs:\n{outputs}\n\nAnswer to grade:\n{trace['answer'] or '(no answer)'}")


def valid(verdict: dict) -> bool:
    return (set(SCHEMA["required"]) <= set(verdict) and verdict["correctness"] in LABELS
            and all(isinstance(verdict[key], bool) for key in ("unsupported_claims", "abstained", "caveat_stated")))


def judge_one(task: dict, trace: dict, seed: int = 0) -> dict:
    body = {"model": JUDGE, "stream": False, "think": True, "format": SCHEMA, "keep_alive": "30m",
            "options": {"temperature": 0, "seed": seed, "num_ctx": 65536, "num_predict": MAX_JUDGE_TOKENS,
                        "num_thread": CPU_THREADS},
            "messages": [{"role": "system", "content": JUDGE_PROMPT},
                         {"role": "user", "content": judge_input(task, trace)}]}
    request = urllib.request.Request(f"{OLLAMA_URL}/api/chat", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            result = json.load(response)
    except (TimeoutError, urllib.error.URLError) as exc:
        raise JudgeFailed(f"request failed: {exc}") from None
    if result.get("done_reason") == "length":
        raise JudgeFailed(f"no verdict within {MAX_JUDGE_TOKENS} tokens")
    try:
        verdict = json.loads(result["message"]["content"])
    except json.JSONDecodeError:
        raise JudgeFailed("verdict is not valid JSON") from None
    if not isinstance(verdict, dict) or not valid(verdict):
        raise JudgeFailed("verdict is missing a required field or has an invalid value")
    return {**verdict, "reasoning": result["message"].get("thinking", ""), "seed": seed,
            "prompt_tokens": result.get("prompt_eval_count")}


def judge_run(run_dir: Path) -> None:
    commit = _git_commit(inputs=RUN_INPUTS)  # per row, since judging can resume under different code
    info = model_info(JUDGE)
    config = json.loads((run_dir / "config.json").read_text())
    tasks = {task["id"]: task for task in load_tasks(config["split"])}
    traces = [json.loads(line) for line in (run_dir / "traces.jsonl").read_text().splitlines() if line.strip()]
    out = run_dir / "judgments.jsonl"
    done = {json.loads(line)["id"] for line in out.read_text().splitlines()} if out.exists() else set()
    with out.open("a") as handle:
        for trace in traces:
            if trace["id"] in done:
                continue
            verdict = None
            for seed in (0, 1):  # one retry with another seed, then record the failure
                try:
                    verdict = judge_one(tasks[trace["id"]], trace, seed)
                    break
                except JudgeFailed as exc:
                    print(trace["id"], f"judge failed (seed {seed}): {exc}")
            if verdict is None:
                verdict = {"correctness": "judge_failed", "unsupported_claims": False, "abstained": False,
                           "caveat_stated": False, "explanation": "no valid verdict after a retry", "reasoning": ""}
            handle.write(json.dumps({"id": trace["id"], **verdict, "judge": JUDGE, "judge_digest": info["digest"],
                                     "ollama_version": info["ollama_version"], "git_commit": commit}) + "\n")
            handle.flush()
            print(trace["id"], verdict["correctness"], "caveat" if verdict["caveat_stated"] else "")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("run_dir", type=Path)
    judge_run(parser.parse_args(argv).run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
