"""Secondary baseline: the A2 RAG pipeline (gemma4, documents only, no data tools) on the A3 tasks.

    uv run --extra models python -m resplens.agent.baseline --split test

Writes a run directory in the agent's trace format, with the retrieved passages recorded as one search_docs call,
so `run score` and `judge` apply unchanged. Injections are not applied: the baseline has no tool loop to attack.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime

from ..data import DATA_TAG
from ..retrieval import answer, corpus
from ..retrieval.evaluate import ROOT, _git_commit
from .run import RUN_INPUTS, load_tasks, model_info


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--split", default="test", choices=["dev", "test"])
    split = parser.parse_args(argv).split
    commit = _git_commit(inputs=RUN_INPUTS)
    tasks = load_tasks(split)
    contexts = answer.rag_contexts(tasks, corpus.load())
    import gc, torch  # free GPU memory used by the retrieval models before loading the generator
    gc.collect()
    torch.cuda.empty_cache()

    run_dir = ROOT / "eval" / "agent-runs" / f"{datetime.now():%Y%m%d-%H%M%S}-{split}-rag-seed0"
    run_dir.mkdir(parents=True)
    config = {"split": split, "system": "rag", **model_info(answer.GENERATOR), "think": False, "seed": 0,
              "temperature": 0, "num_ctx": answer.RAG_CONTEXT, "max_output": answer.MAX_OUTPUT,
              "system_prompt": answer.SYSTEM_PROMPT, "rag_top_k": answer.RAG_TOP_K, "chunk_tokens": answer.CHUNK_TOKENS,
              "retrieval": "hybrid bm25 + BAAI/bge-m3, rerank BAAI/bge-reranker-v2-m3", "data_release": DATA_TAG,
              "corpus_manifest_sha256": hashlib.sha256((ROOT / "corpus" / "manifest.csv").read_bytes()).hexdigest(),
              "task_ids": [task["id"] for task in tasks], "git_commit": commit,
              "started": datetime.now().isoformat(timespec="seconds")}
    (run_dir / "config.json").write_text(json.dumps(config, indent=1))
    with (run_dir / "traces.jsonl").open("w") as handle:
        for task in tasks:
            context = contexts[task["id"]]
            prompt = answer.format_documents(context["items"]) + f"\n\nQuestion: {task['question']}"
            result = answer.chat([{"role": "system", "content": answer.SYSTEM_PROMPT},
                                  {"role": "user", "content": prompt}], answer.RAG_CONTEXT)
            passages = {"results": [{"chunk_id": chunk, "doc_id": doc_id, "text": text}
                                    for chunk, (doc_id, text) in zip(context["chunks"], context["items"])]}
            call = {"name": "search_docs", "args": {"query": task["question"]},
                    "output": json.dumps(passages, indent=2), "is_error": False}
            trace = {"id": task["id"], "question": task["question"], "answer": result["message"]["content"].strip(),
                     "stop": "answer", "turns": [{"tool_calls": [call]}], "model_turns": 1, "tool_calls": 1,
                     "parallel_batches": 0, "tool_errors": 0, "prompt_tokens": result.get("prompt_eval_count"),
                     "output_tokens": result.get("eval_count"),
                     "seconds": round(result["wall_seconds"] + context["retrieval_seconds"], 3)}
            handle.write(json.dumps(trace) + "\n")
            handle.flush()
            print(f"{task['id']} {trace['seconds']:.1f}s")
    print(f"saved to {run_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
