"""Score generated answers with an LLM judge, and prepare a blind human calibration sheet.

    uv run python -m resplens.retrieval.judge score eval/answers/<run>
    uv run python -m resplens.retrieval.judge sample eval/answers/<run>   # 15 answers for human scoring
    uv run python -m resplens.retrieval.judge report eval/answers/<run>
"""

from __future__ import annotations

import argparse
import json
import random
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

from . import corpus
from .dense import OLLAMA_URL
from .evaluate import load_questions


JUDGE = "qwen3:235b-thinking"
LABELS = ("correct", "partial", "incorrect")

JUDGE_PROMPT = """You grade an answer to a question about US respiratory surveillance documentation.
You are given the question, a reference answer written by a human, the evidence sentences that support
the reference answer, the full text of the source documents that contain the evidence, and the answer to grade.

- correctness: judge the facts the question asks for; details in the reference answer beyond what the question
  asks are not required.
  "correct" if the answer gives every fact the question asks for, consistent with the reference answer (wording
  may differ; extra detail is fine if it does not contradict the reference or evidence).
  "partial" if it gives some of the asked-for facts correctly but misses others, including saying the documents
  do not state one part, or hedges where the reference is definite.
  "incorrect" if an asked-for fact is wrong or contradicts the reference or evidence, or if the answer gives none
  of the asked-for facts (for example, says the documents do not answer the question at all).
  Extra details beyond what the question asks never lower correctness; they matter only for unsupported_claims.
- unsupported_claims: true if the answer states a specific fact (a number, date, rule, procedure, or definition)
  that is supported by none of the reference answer, the evidence, or the source documents. Restating the
  question or citing document IDs does not count.
- abstained: true if the answer says the documents do not answer the question.

Return JSON only."""

SCHEMA = {"type": "object", "properties": {
    "correctness": {"type": "string", "enum": list(LABELS)},
    "unsupported_claims": {"type": "boolean"},
    "abstained": {"type": "boolean"},
    "explanation": {"type": "string"}},
    "required": ["correctness", "unsupported_claims", "abstained", "explanation"]}


MAX_JUDGE_TOKENS = 8192  # thinking plus the JSON verdict; one test item ran without stopping before this cap existed


class JudgeFailed(RuntimeError):
    pass


def judge_one(question: dict, answer: str, documents: dict[str, str], seed: int = 0) -> dict:
    evidence = "\n".join(f"- ({item['doc']}) {item['quote']}" for item in question["evidence"]) or "(none)"
    sources = "\n\n".join(f"<document id='{doc}'>\n{documents[doc]}\n</document>"
                           for doc in dict.fromkeys(item["doc"] for item in question["evidence"])) or "(none)"
    user = (f"Question: {question['question']}\n\nReference answer: {question['answer']}\n\n"
            f"Evidence:\n{evidence}\n\nSource documents:\n{sources}\n\nAnswer to grade:\n{answer}")
    body = {"model": JUDGE, "stream": False, "think": True, "format": SCHEMA, "keep_alive": "30m",
            "options": {"temperature": 0, "seed": seed, "num_ctx": 65536, "num_predict": MAX_JUDGE_TOKENS},
            "messages": [{"role": "system", "content": JUDGE_PROMPT}, {"role": "user", "content": user}]}
    request = urllib.request.Request(f"{OLLAMA_URL}/api/chat", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            result = json.load(response)
    except (TimeoutError, urllib.error.URLError) as exc:
        raise JudgeFailed(f"request failed: {exc}") from None
    if result.get("done_reason") == "length":
        raise JudgeFailed(f"no verdict within {MAX_JUDGE_TOKENS} tokens")
    message = result["message"]
    try:
        verdict = json.loads(message["content"])
    except json.JSONDecodeError:
        raise JudgeFailed("verdict is not valid JSON") from None
    return {**verdict, "reasoning": message.get("thinking", ""), "seed": seed}


def _answers(run: Path) -> list[dict]:
    return [json.loads(line) for line in (run / "answers.jsonl").read_text().splitlines() if line.strip()]


def score(run: Path) -> None:
    config = json.loads((run / "config.json").read_text())
    questions = {q["id"]: q for q in load_questions(split=config["split"])}
    documents = {doc.id: doc.text for doc in corpus.load()}
    out = run / "judgments.jsonl"
    done = {(row["id"], row["system"]) for row in map(json.loads, out.read_text().splitlines())} if out.exists() else set()
    with out.open("a") as handle:
        for row in _answers(run):
            if (row["id"], row["system"]) in done:
                continue
            verdict = None
            for seed in (0, 1):  # one retry with another seed, then record the failure
                try:
                    verdict = judge_one(questions[row["id"]], row["answer"], documents, seed)
                    break
                except JudgeFailed as exc:
                    print(row["id"], row["system"], f"judge failed (seed {seed}): {exc}")
            if verdict is None:
                verdict = {"correctness": "judge_failed", "unsupported_claims": False, "abstained": False,
                           "explanation": "judge produced no verdict after a retry", "reasoning": ""}
            handle.write(json.dumps({"id": row["id"], "system": row["system"], **verdict}) + "\n")
            handle.flush()
            print(row["id"], row["system"], verdict["correctness"], "unsupported" if verdict["unsupported_claims"] else "")


def sample(run: Path, n: int = 15, seed: int = 20261022) -> None:
    """Blind sheet: answers stratified by system and question type, shuffled, system labels hidden."""
    config = json.loads((run / "config.json").read_text())
    questions = {q["id"]: q for q in load_questions(split=config["split"])}
    rng = random.Random(seed)
    strata = defaultdict(list)
    for row in _answers(run):
        strata[(row["system"], questions[row["id"]]["type"])].append(row)
    for rows in strata.values():
        rng.shuffle(rows)
    # alternate systems within each question type, so both systems get about half the sample
    picked, keys = [], sorted(strata, key=lambda key: (key[1], key[0]))
    while len(picked) < n and any(strata[key] for key in keys):
        for key in keys:
            if strata[key] and len(picked) < n:
                picked.append(strata[key].pop())
    rng.shuffle(picked)
    rubric = JUDGE_PROMPT[JUDGE_PROMPT.index("- correctness:"):JUDGE_PROMPT.index("Return JSON only.")].strip()
    key_rows, lines = [], ["# Human calibration sheet", "",
                           "For each answer, fill in **correctness** (`correct`, `partial`, or `incorrect`) and "
                           "**unsupported** (`yes` or `no`). The system that produced each answer and the judge's grade "
                           "are hidden. Use the same rules as the judge; the source documents are in `corpus/text/` "
                           "(document IDs as shown with each evidence quote).", "", "Rules given to the judge:", "",
                           *[f"> {line}" for line in rubric.splitlines()], ""]
    for number, row in enumerate(picked, start=1):
        question = questions[row["id"]]
        evidence = "<br>".join(f"`{e['doc']}`: \"{e['quote']}\"" for e in question["evidence"]) or "(none: unanswerable)"
        lines += [f"## H{number:02d}", "", f"**Question:** {question['question']}", "",
                  f"**Reference answer:** {question['answer']}", "", f"**Evidence:** {evidence}", "",
                  f"**Answer to grade:** {row['answer']}", "", "**correctness:** ", "", "**unsupported:** ", ""]
        key_rows.append({"sheet_id": f"H{number:02d}", "id": row["id"], "system": row["system"]})
    (run / "human-review.md").write_text("\n".join(lines))
    (run / "human-key.jsonl").write_text("".join(json.dumps(row) + "\n" for row in key_rows))
    print(f"wrote {run / 'human-review.md'} ({len(picked)} answers)")


def _sign_test(gain: int, loss: int) -> float:
    n = gain + loss
    return min(1.0, sum(comb(n, i) for i in range(min(gain, loss) + 1)) * 2 / 2 ** n) if n else 1.0


def report(run: Path) -> dict:
    config = json.loads((run / "config.json").read_text())
    questions = {q["id"]: q for q in load_questions(split=config["split"])}
    answers = {(row["id"], row["system"]): row for row in _answers(run)}
    judged = {(row["id"], row["system"]): row for row in map(json.loads, (run / "judgments.jsonl").read_text().splitlines())}
    summary = {}
    for system in ("rag", "long_context"):
        answerable = [qid for qid in questions if questions[qid]["evidence"]]
        unanswerable = [qid for qid in questions if not questions[qid]["evidence"]]
        labels = Counter(judged[(qid, system)]["correctness"] for qid in answerable)
        cites = [bool(set(answers[(qid, system)]["cited"]) & {e["doc"] for e in questions[qid]["evidence"]})
                 for qid in answerable]
        rows = [answers[(qid, system)] for qid in questions]
        summary[system] = {
            "answerable": len(answerable), **{label: labels[label] for label in LABELS},
            "judge_failed": labels["judge_failed"],
            "correct_rate": round(labels["correct"] / len(answerable), 3),
            "unsupported_rate": round(sum(judged[(q, system)]["unsupported_claims"] for q in answerable) / len(answerable), 3),
            "abstained_on_unanswerable": f"{sum(judged[(q, system)]['abstained'] for q in unanswerable)}/{len(unanswerable)}",
            "wrongly_abstained": sum(judged[(q, system)]["abstained"] for q in answerable),
            "citation_recall": round(sum(cites) / len(cites), 3),
            "median_prompt_tokens": sorted(r["prompt_tokens"] for r in rows)[len(rows) // 2],
            "median_seconds": sorted(r["seconds"] for r in rows if not r.get("cold"))[len([r for r in rows if not r.get("cold")]) // 2],
        }
        if system == "long_context":
            cold = [r["seconds"] for r in rows if r.get("cold")]
            summary[system]["cold_seconds"] = cold
    ids = [qid for qid in questions if questions[qid]["evidence"]]
    rag = [judged[(q, "rag")]["correctness"] == "correct" for q in ids]
    long = [judged[(q, "long_context")]["correctness"] == "correct" for q in ids]
    gain, loss = sum(l and not r for r, l in zip(rag, long)), sum(r and not l for r, l in zip(rag, long))
    summary["long_vs_rag_correct"] = {"long_only": gain, "rag_only": loss, "sign_test_p": round(_sign_test(gain, loss), 3)}
    if (run / "human-review.md").exists():
        summary["human_agreement"] = agreement(run, judged)
    print(json.dumps(summary, indent=1))
    (run / "report.json").write_text(json.dumps(summary, indent=1))
    return summary


def agreement(run: Path, judged: dict) -> dict:
    """Agreement and Cohen's kappa between human and judge correctness labels on the calibration sheet."""
    keys = {row["sheet_id"]: row for row in map(json.loads, (run / "human-key.jsonl").read_text().splitlines())}
    human, current = {}, None
    for line in (run / "human-review.md").read_text().splitlines():
        if line.startswith("## H"):
            current = line[3:].strip()
        elif line.startswith("**correctness:**") and current:
            label = line.split("**correctness:**", 1)[1].strip().lower()
            if label in LABELS:
                human[current] = label
    human = {sid: label for sid, label in human.items()
             if judged[(keys[sid]["id"], keys[sid]["system"])]["correctness"] in LABELS}  # skip judge failures
    pairs = [(label, judged[(keys[sid]["id"], keys[sid]["system"])]["correctness"]) for sid, label in human.items()]
    if not pairs:
        return {"scored": 0}
    observed = sum(a == b for a, b in pairs) / len(pairs)
    expected = sum((sum(a == l for a, _ in pairs) / len(pairs)) * (sum(b == l for _, b in pairs) / len(pairs))
                   for l in LABELS)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    return {"scored": len(pairs), "agreement": round(observed, 3), "cohen_kappa": round(kappa, 3),
            "disagreements": [(sid, h, j) for (sid, h), (_, j) in zip(human.items(), pairs) if h != j]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["score", "sample", "report"])
    parser.add_argument("run", type=Path)
    args = parser.parse_args(argv)
    {"score": score, "sample": sample, "report": report}[args.command](args.run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
