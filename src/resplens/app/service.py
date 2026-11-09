"""Local agent service (design: docs/deploy.md, "A. Local service").

    uv sync --extra app --extra models
    uv run resplens-app            # http://127.0.0.1:8000

Runs the unchanged A3 loop (`agent.loop.run_task`, A3 system prompt and tools) against a local Ollama, streams each
step as server-sent events, checks the numbers in the answer as the evaluation does, and appends one line per query
to logs/queries.jsonl. One question at a time.

Environment: OLLAMA_URL (default http://127.0.0.1:11434); RESPLENS_OTHER_MODEL adds a system running another Ollama
model with thinking off (marked as not evaluated); RESPLENS_LOG_QUESTIONS=0 leaves question text out of the log;
RESPLENS_HOST and RESPLENS_PORT set the address (default 127.0.0.1:8000).
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from mcp import Client
from pydantic import BaseModel

from .. import server
from ..agent import checks, loop
from ..agent.run import SYSTEMS, model_info
from ..retrieval.evaluate import ROOT

STATIC = Path(__file__).parent / "static"
MAX_QUESTION = 1000
SEED = 0  # the evaluation's first run
LOG = ROOT / "logs" / "queries.jsonl"

Emit = Callable[[dict], None]


def systems() -> dict:
    out = {name: {**spec, "evaluated": True} for name, spec in SYSTEMS.items()}
    other = os.environ.get("RESPLENS_OTHER_MODEL")
    if other:
        out["other"] = {"model": other, "think": False, "evaluated": False}
    return out


class StreamingToolbox(loop.Toolbox):
    """The A3 toolbox, reporting each tool output as it is produced."""

    emit: Emit = staticmethod(lambda event: None)

    async def call(self, name: str, args: dict) -> tuple[str, bool]:
        output, is_error = await super().call(name, args)
        self.emit({"type": "tool_output", "name": name, "args": args, "output": output, "is_error": is_error})
        return output, is_error


def streaming_chat(chat_fn, emit: Emit):
    """Wrap the loop's chat function so each model turn is reported; the request and reply are unchanged."""
    def chat(model, messages, tools, think, seed):
        emit({"type": "model_start"})
        result = chat_fn(model, messages, tools, think, seed)
        message = result["message"]
        emit({"type": "model_turn", "content": message.get("content") or "", "thinking": message.get("thinking") or "",
              "tool_calls": [{"name": c["function"]["name"], "args": c["function"].get("arguments")}
                             for c in message.get("tool_calls") or []],
              "prompt_tokens": result.get("prompt_eval_count"), "output_tokens": result.get("eval_count"),
              "seconds": round(result["wall_seconds"], 3)})
        return result
    return chat


class Service:
    def __init__(self, chat_fn=loop.chat, search=None, client_factory=lambda: Client(server.mcp), log_path: Path = LOG,
                 log_questions: bool | None = None, info=model_info):
        self.chat_fn, self.client_factory, self.log_path, self.info = chat_fn, client_factory, log_path, info
        self.log_questions = (os.environ.get("RESPLENS_LOG_QUESTIONS", "1") != "0" if log_questions is None
                              else log_questions)
        self.systems = systems()
        self.lock = threading.Lock()  # one question at a time
        self._search, self._search_lock = search, threading.Lock()

    def search(self, query: str) -> list[dict]:
        """The A2 retriever, loaded on the first search and kept for later questions."""
        with self._search_lock:
            if self._search is None:
                self._search = loop.document_search()
        return self._search(query)

    async def run(self, question: str, system: str, emit: Emit) -> dict:
        spec = self.systems[system]
        emit({"type": "start", "system": system, "model": spec["model"], "evaluated": spec["evaluated"]})
        async with self.client_factory() as client:
            toolbox = await StreamingToolbox.create(client, search=self.search)
            toolbox.emit = emit
            trace = await loop.run_task({"id": "live", "question": question}, toolbox, spec["model"], spec["think"],
                                        SEED, chat_fn=streaming_chat(self.chat_fn, emit))
        result = trace.to_dict()
        check = checks.grounding(result["answer"], question, [call["output"] for call in trace.calls()])
        emit({"type": "answer", "answer": result["answer"], "stop": result["stop"], "direct": check["direct"],
              "not_found": check["unmatched"], "seconds": result["seconds"],
              "prompt_tokens": result["prompt_tokens"], "output_tokens": result["output_tokens"]})
        self.log(question, system, spec, result, check)
        return result

    def log(self, question: str, system: str, spec: dict, result: dict, check: dict) -> None:
        try:
            digest = self.info(spec["model"])["digest"]
        except OSError:
            digest = None
        calls = [call for turn in result["turns"] for call in turn["tool_calls"]]
        line = {"time": datetime.now().astimezone().isoformat(timespec="seconds"), "system": system,
                "model": spec["model"], "digest": digest, "evaluated": spec["evaluated"],
                "question": question if self.log_questions else None, "seconds": result["seconds"],
                "prompt_tokens": result["prompt_tokens"], "output_tokens": result["output_tokens"],
                "model_turns": result["model_turns"], "tools": [call["name"] for call in calls],
                "tool_errors": result["tool_errors"], "stop": result["stop"],
                "numbers_found": len(check["direct"]), "numbers_not_found": check["unmatched"]}
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a") as handle:
            handle.write(json.dumps(line) + "\n")


class Ask(BaseModel):
    question: str
    system: str = "gemma"


def create_app(service: Service | None = None) -> FastAPI:
    service = service or Service()
    app = FastAPI(title="resplens agent", docs_url=None, redoc_url=None)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/api/systems")
    def list_systems() -> dict:
        return {name: {"model": spec["model"], "evaluated": spec["evaluated"]} for name, spec in service.systems.items()}

    @app.post("/api/ask")
    def ask(body: Ask) -> StreamingResponse:
        question = body.question.strip()
        if not question or len(question) > MAX_QUESTION:
            raise HTTPException(422, f"The question must have 1 to {MAX_QUESTION} characters.")
        if body.system not in service.systems:
            raise HTTPException(422, f"Unknown system {body.system!r}.")
        if not service.lock.acquire(blocking=False):
            raise HTTPException(429, "Another question is running; try again when it has finished.")
        events: queue.Queue = queue.Queue()

        def work() -> None:
            try:
                asyncio.run(service.run(question, body.system, events.put))
            except Exception as exc:  # reported to the page; the query is not logged
                while isinstance(exc, ExceptionGroup) and len(exc.exceptions) == 1:  # raised inside the MCP client
                    exc = exc.exceptions[0]
                events.put({"type": "error", "message": f"{type(exc).__name__}: {exc}"})
            finally:
                service.lock.release()
                events.put(None)

        threading.Thread(target=work, daemon=True).start()

        def stream():
            while (event := events.get()) is not None:
                yield f"data: {json.dumps(event)}\n\n"
        return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "live.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


def main() -> None:
    import uvicorn
    uvicorn.run(create_app(), host=os.environ.get("RESPLENS_HOST", "127.0.0.1"),
                port=int(os.environ.get("RESPLENS_PORT", "8000")))


if __name__ == "__main__":
    main()
