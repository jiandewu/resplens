"""An LLM as forecaster: the series as text in, 23 quantiles per target week out (plan: docs/llm-forecast-eval.md)."""

from __future__ import annotations

import json
import math
import time
import urllib.request
from datetime import date, timedelta

from ..retrieval.dense import CPU_THREADS, OLLAMA_URL
from .persistence import LEVELS
from .vintage import Series


NUM_CTX = 20_480
MAX_OUTPUT = 16_384  # includes reasoning tokens; gpt-oss used 7,941 of 8,192 on one smoke-test forecast
# Prompt variants compared on dev: weeks of history, and whether the same weeks one year earlier are added.
VARIANTS = {"h26": (26, False), "h26_last_year": (26, True), "h52": (52, False)}
KEYS = [f"week_{i}" for i in range(1, 5)]
SCHEMA = {"type": "object",
          "properties": {key: {"type": "array", "items": {"type": "number"}, "minItems": len(LEVELS),
                               "maxItems": len(LEVELS)} for key in KEYS},
          "required": KEYS}

SYSTEM_PROMPT = "You forecast weekly counts of hospital admissions. Use only the data you are given."


def _lines(series: Series) -> str:
    return "\n".join(f"{week}: {'missing' if value is None else value}" for week, value in series)


def prompt(state_name: str, state: str, pathogen: str, forecast_date: str, series: Series, targets: list[str],
           variant: str) -> str:
    weeks, last_year = VARIANTS[variant]
    recent = series[-weeks:]
    text = [f"State: {state_name} ({state}). Pathogen: {pathogen}.",
            "Measure: weekly new hospital admissions with a laboratory-confirmed diagnosis, all ages, as reported to "
            "CDC's National Healthcare Safety Network (NHSN). Weeks end on Saturday.",
            f"Forecast date: {forecast_date}. The data end with the week ending {series[-1][0]}.", "",
            f"Weekly admissions, last {len(recent)} weeks:", _lines(recent)]
    if last_year:
        values = dict(series)
        wanted = [*[week for week, _ in series[-4:]], *targets]
        earlier = [((date.fromisoformat(w) - timedelta(weeks=52)).isoformat()) for w in wanted]
        text += ["", "The same weeks one year earlier:", _lines([(w, values.get(w)) for w in earlier])]
    levels = ", ".join(f"{level:g}" for level in LEVELS)
    text += ["", "Forecast the admissions for these weeks: "
             + "; ".join(f"{key} = week ending {week}" for key, week in zip(KEYS, targets)) + ".",
             f"For each week give {len(LEVELS)} quantiles of your forecast distribution, at the levels {levels}, "
             "in increasing order.",
             f"Return JSON with the keys {', '.join(KEYS)}, each a list of exactly {len(LEVELS)} numbers."]
    return "\n".join(text)


def chat(model: str, messages: list[dict], think: bool | str, seed: int = 0) -> dict:
    body = {"model": model, "messages": messages, "stream": False, "think": think, "format": SCHEMA,
            "keep_alive": "30m",
            "options": {"temperature": 0, "seed": seed, "num_ctx": NUM_CTX, "num_predict": MAX_OUTPUT,
                        "num_thread": CPU_THREADS}}
    request = urllib.request.Request(f"{OLLAMA_URL}/api/chat", json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=1800) as response:
        result = json.load(response)
    result["wall_seconds"] = time.perf_counter() - start
    return result


def parse(result: dict) -> tuple[dict | None, str | None]:
    """Quantiles per key, or the error to send back to the model."""
    if result.get("done_reason") == "length":
        return None, f"the answer was cut off at the {MAX_OUTPUT}-token limit; answer more briefly"
    try:
        answer = json.loads(result["message"].get("content") or "")
    except json.JSONDecodeError:
        return None, "the answer is not valid JSON"
    if not isinstance(answer, dict):
        return None, "the answer must be a JSON object"
    out = {}
    for key in KEYS:
        values = answer.get(key)
        if not isinstance(values, list):
            return None, f"{key} is missing or not a list"
        if len(values) != len(LEVELS):
            return None, f"{key} has {len(values)} values; return exactly {len(LEVELS)}"
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values):
            return None, f"{key} contains a value that is not a finite number"
        out[key] = [float(v) for v in values]
    return out, None


def clean(quantiles: list[float]) -> tuple[list[float], bool, bool]:
    """Sorted and clipped at 0, with whether sorting and clipping were needed."""
    unsorted = any(b < a for a, b in zip(quantiles, quantiles[1:]))
    negative = any(v < 0 for v in quantiles)
    return sorted(max(0.0, v) for v in quantiles), unsorted, negative


def forecast(model: str, think: bool | str, text: str, targets: list[str], chat_fn=chat) -> dict:
    """One forecast with at most one repair turn. Returns the cleaned quantiles per target week (None on failure)
    and everything needed to audit it."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}]
    turns = []
    for attempt in range(2):
        result = chat_fn(model, messages, think)
        message = result["message"]
        parsed, error = parse(result)
        turns.append({"content": message.get("content") or "", "thinking": message.get("thinking") or "",
                      "done_reason": result.get("done_reason"), "error": error,
                      "prompt_tokens": result.get("prompt_eval_count"), "output_tokens": result.get("eval_count"),
                      "seconds": round(result["wall_seconds"], 3)})
        if parsed:
            out, unsorted, negative = {}, False, False
            for key, week in zip(KEYS, targets):
                out[week], was_unsorted, was_negative = clean(parsed[key])
                unsorted, negative = unsorted or was_unsorted, negative or was_negative
            return {"quantiles": out, "repaired": attempt == 1, "sorted": unsorted, "clipped": negative,
                    "turns": turns}
        messages += [{"role": "assistant", "content": message.get("content") or ""},
                     {"role": "user", "content": f"Your answer could not be used: {error}. Return JSON with the keys "
                                                 f"{', '.join(KEYS)}, each a list of exactly {len(LEVELS)} numbers "
                                                 "in increasing order."}]
    return {"quantiles": None, "repaired": True, "sorted": False, "clipped": False, "turns": turns}
