import json

from resplens.agent import judge
from resplens.forecast import tool_eval

FORECAST = {"state": "AA", "pathogen": "influenza",
            "forecasts": [{"week": "2026-10-17", "median": 60, "interval_95": [23, 117]}],
            "notes": ["In the backtest the 95% intervals held the reported value 90.2% of the time."]}
TASK = {"id": "f99", "type": "forecast_basic", "question": "Forecast influenza in AA.",
        "expected_calls": [{"tool": "forecast_admissions", "args": {"state": "AA", "pathogen": "influenza"}}],
        "alternatives": {}, "forbidden_calls": [], "required_numbers": [60, 23, 117], "requires_caveat": True,
        "evidence": []}


def trace(answer, calls):
    return {"id": "f99", "answer": answer, "stop": "answer",
            "turns": [{"tool_calls": [{"name": n, "args": a, "output": json.dumps(o), "is_error": False}
                                      for n, a, o in calls]}],
            **{k: 0 for k in ("model_turns", "tool_calls", "parallel_batches", "tool_errors", "prompt_tokens",
                              "output_tokens", "seconds")}}


def test_check_passes_a_complete_forecast_answer_and_uses_the_prompt_as_a_source():
    call = ("forecast_admissions", {"state": "aa", "pathogen": "influenza"}, FORECAST)
    row = tool_eval.check(TASK, trace("Model forecast: 60 (95% interval 23 to 117); 4 weeks ahead.", [call]),
                          "Forecasts cover 1 to 4 weeks.", {"AA-influenza": FORECAST})
    assert row["extra_failures"] == [] and row["direct_grounding_pass"] and row["forecast_output_mismatch"] == []


def test_check_reports_missing_forecast_call_numbers_and_forbidden_calls():
    row = tool_eval.check(TASK, trace("About 60.", []), "", {})
    assert row["extra_failures"][0].startswith("forecast_call_missing")
    assert "required_numbers_missing=[23, 117]" in row["extra_failures"]
    task = {**TASK, "expected_calls": [], "required_numbers": [], "forbidden_calls": [{"tool": "forecast_admissions"}]}
    call = ("forecast_admissions", {"state": "AA", "pathogen": "influenza"}, FORECAST)
    row = tool_eval.check(task, trace("No forecast needed.", [call]), "", {"AA-influenza": FORECAST})
    assert row["extra_failures"] == ["forbidden_call=['forecast_admissions']"]


def test_check_flags_a_forecast_that_differs_from_the_recorded_output():
    changed = {**FORECAST, "forecasts": [{**FORECAST["forecasts"][0], "median": 61}]}
    call = ("forecast_admissions", {"state": "AA", "pathogen": "influenza"}, changed)
    row = tool_eval.check(TASK, trace("61", [call]), "", {"AA-influenza": FORECAST})
    assert row["forecast_output_mismatch"] == ["AA-influenza"]


def test_judge_prompt_adds_the_forecast_rule_before_the_json_instruction():
    prompt = tool_eval.judge_prompt()
    assert prompt.startswith(judge.JUDGE_PROMPT[:-len("Return JSON only.")].rstrip())
    assert "model forecast" in prompt and prompt.endswith("\n\nReturn JSON only.")


def test_thousands_with_narrow_spaces_and_tool_error_messages_count_as_sources():
    big = {**FORECAST, "forecasts": [{"week": "2026-10-17", "median": 1086, "interval_95": [293, 2641]}]}
    task = {**TASK, "required_numbers": [1086, 293, 2641]}
    calls = [("forecast_admissions", {"state": "AA", "pathogen": "influenza"}, big)]
    t = trace("Median 1 086 (95% interval 293 – 2 641).", calls)
    t["turns"][0]["tool_calls"].append({"name": "forecast_admissions", "args": {"state": "ZZ", "pathogen": "rsv"},
                                        "output": "No forecast for ZZ rsv: fewer than 26 reported weeks among the "
                                                  "last 52.", "is_error": True})
    t["answer"] += " ZZ has fewer than 26 of the last 52 weeks."
    row = tool_eval.check(task, t, "", {"AA-influenza": big})
    assert row["extra_failures"] == [] and row["numbers"]["unmatched"] == []
