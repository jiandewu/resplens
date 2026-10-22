"""Generate answers from retrieved passages (RAG) or from the whole corpus (long context).

    uv run --extra models python -m resplens.retrieval.answer --split dev
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from . import corpus
from .dense import OLLAMA_URL, SentenceTransformerEmbedder, dense_search, hybrid_search, rerank_search
from .evaluate import ROOT, _git_commit, bm25_search, build_chunks, load_questions


GENERATOR = "gemma4:31b"
LONG_CONTEXT = 262_144
RAG_CONTEXT = 16_384
MAX_OUTPUT = 1024
RAG_TOP_K = 5
CHUNK_TOKENS = 300

SYSTEM_PROMPT = """You answer questions about US respiratory surveillance data using only the documents provided.
Rules:
- Use only information stated in the documents. Do not use outside knowledge.
- If the documents do not answer the question, reply exactly: "The documents do not answer this question."
- Be concise: one to three sentences.
- End with one line listing the IDs of the documents you used, in the form: Sources: <id>, <id>"""


class ContextOverflow(RuntimeError):
    pass


def format_documents(items: list[tuple[str, str]]) -> str:
    return "\n\n".join(f"<document id='{doc_id}'>\n{text}\n</document>" for doc_id, text in items)


def chat(messages: list[dict], num_ctx: int, keep_alive: str | int = "30m") -> dict:
    body = {"model": GENERATOR, "messages": messages, "stream": False, "think": False, "keep_alive": keep_alive,
            "options": {"num_ctx": num_ctx, "num_predict": MAX_OUTPUT, "temperature": 0, "seed": 0}}
    request = urllib.request.Request(f"{OLLAMA_URL}/api/chat", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=3600) as response:
        result = json.load(response)
    result["wall_seconds"] = time.perf_counter() - start
    prompt, output = result.get("prompt_eval_count", 0), result.get("eval_count", 0)
    # A prompt that fills the window leaves no room for the answer: the server then drops earlier
    # context while generating, without an error (observed: an invented quote at num_ctx 131,072).
    if prompt + MAX_OUTPUT > num_ctx:
        raise ContextOverflow(f"prompt {prompt} + output limit {MAX_OUTPUT} exceeds num_ctx {num_ctx}")
    return result


def unload() -> None:
    """Drop the model from memory so the next call is a cold start."""
    body = json.dumps({"model": GENERATOR, "keep_alive": 0}).encode()
    request = urllib.request.Request(f"{OLLAMA_URL}/api/generate", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600):
        pass


def cited_documents(answer: str) -> list[str]:
    match = re.search(r"Sources?:\s*(.+)\s*$", answer.strip(), flags=re.IGNORECASE)
    return [part.strip(" `'\".") for part in match.group(1).split(",") if part.strip()] if match else []


def rag_contexts(questions: list[dict], documents: list[corpus.Document]) -> dict[str, dict]:
    """Retrieved chunks per question, computed before generation so the retrieval models can be freed."""
    chunks = build_chunks(documents, CHUNK_TOKENS)
    texts = [chunk.indexed_text() for chunk in chunks]
    embedder = SentenceTransformerEmbedder("BAAI/bge-m3")
    search = rerank_search(hybrid_search([bm25_search(chunks), dense_search(embedder, texts)]), texts)
    contexts = {}
    for question in questions:
        start = time.perf_counter()
        ranked = search(question["question"], RAG_TOP_K)
        contexts[question["id"]] = {"retrieval_seconds": time.perf_counter() - start,
                                    "chunks": [chunks[index].id for index in ranked],
                                    "items": [(chunks[index].doc_id, texts[index]) for index in ranked]}
    return contexts


def generate(split: str, cold_runs: int = 3) -> Path:
    documents = corpus.load()
    questions = load_questions(split=split)
    run_dir = ROOT / "eval" / "answers" / f"{datetime.now():%Y%m%d-%H%M%S}-{split}"
    run_dir.mkdir(parents=True)
    rows = []

    contexts = rag_contexts(questions, documents)
    import gc, torch  # free GPU memory used by the retrieval models before loading the generator
    gc.collect()
    torch.cuda.empty_cache()

    for question in questions:
        context = contexts[question["id"]]
        prompt = format_documents(context["items"]) + f"\n\nQuestion: {question['question']}"
        result = chat([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], RAG_CONTEXT)
        answer = result["message"]["content"].strip()
        rows.append({"id": question["id"], "system": "rag", "answer": answer, "cited": cited_documents(answer),
                     "retrieved_chunks": context["chunks"], "prompt_tokens": result.get("prompt_eval_count"),
                     "output_tokens": result.get("eval_count"),
                     "seconds": round(result["wall_seconds"] + context["retrieval_seconds"], 3)})
        print(f"rag  {question['id']} {rows[-1]['seconds']:.1f}s")

    # Documents first and the question last, so the document prefix can be cached between questions.
    whole = format_documents([(doc.id, doc.text) for doc in documents])
    for position, question in enumerate(questions):
        cold = position < cold_runs
        if cold:
            unload()
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": whole + f"\n\nQuestion: {question['question']}"}]
        result = chat(messages, LONG_CONTEXT)
        answer = result["message"]["content"].strip()
        rows.append({"id": question["id"], "system": "long_context", "answer": answer,
                     "cited": cited_documents(answer), "cold": cold,
                     "prompt_tokens": result.get("prompt_eval_count"), "output_tokens": result.get("eval_count"),
                     "load_seconds": round(result.get("load_duration", 0) / 1e9, 3),
                     "seconds": round(result["wall_seconds"], 3)})
        print(f"long {question['id']} {'cold' if cold else 'warm'} {rows[-1]['seconds']:.1f}s")

    config = {"split": split, "generator": GENERATOR, "system_prompt": SYSTEM_PROMPT, "rag_top_k": RAG_TOP_K,
              "chunk_tokens": CHUNK_TOKENS, "retrieval": "hybrid bm25 + BAAI/bge-m3, rerank BAAI/bge-reranker-v2-m3",
              "num_ctx": {"rag": RAG_CONTEXT, "long_context": LONG_CONTEXT}, "max_output": MAX_OUTPUT,
              "temperature": 0, "cold_runs": cold_runs, "git_commit": _git_commit()}
    (run_dir / "config.json").write_text(json.dumps(config, indent=1))
    (run_dir / "answers.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    print(f"saved to {run_dir.relative_to(ROOT)}")
    return run_dir


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--cold-runs", type=int, default=3, help="long-context questions measured from a cold start")
    args = parser.parse_args(argv)
    generate(args.split, args.cold_runs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
