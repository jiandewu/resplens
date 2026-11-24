import asyncio
import json
import random

from resplens.agent import counterfactual as cf
from resplens.agent import loop

SERIES = {"state": "SC", "measure": "hospital_admission_count", "pathogen": "influenza",
          "weeks": [{"week": "2026-09-26", "value": 30, "flag": "observed_valid"},
                    {"week": "2026-10-03", "value": 0, "flag": "observed_zero"},
                    {"week": "2026-10-10", "value": 51, "flag": "observed_valid"}]}


def test_scale_changes_only_values_of_scaled_measures():
    out = cf.scale(SERIES, 1.4)
    assert [w["value"] for w in out["weeks"]] == [42, 0, 71]
    assert [w["week"] for w in out["weeks"]] == [w["week"] for w in SERIES["weeks"]]
    assert SERIES["weeks"][0]["value"] == 30  # the original is not modified
    reporting = {**SERIES, "measure": "hospital_reporting_count"}
    assert cf.scale(reporting, 1.4) == reporting
    assert cf.scale({"caveats": ["x"]}, 1.4) == {"caveats": ["x"]}


def test_scale_keeps_decimal_places_and_recomputes_revision_percent():
    ed = {"measure": "ed_visit_percent", "weeks": [{"value": 7.9}, {"value": 0.13}, {"value": 2.0}]}
    assert [w["value"] for w in cf.scale(ed, 1.25)["weeks"]] == [9.9, 0.16, 2.5]
    revisions = {"measure": "hospital_admission_count", "first_value": 30, "latest_value": 33,
                 "percent_change_first_to_latest": 10.0, "change_points": [{"value": 30}, {"value": 33}]}
    out = cf.scale(revisions, 0.7)
    assert (out["first_value"], out["latest_value"]) == (21, 23)
    assert [p["value"] for p in out["change_points"]] == [21, 23]
    assert out["percent_change_first_to_latest"] == round((23 - 21) / 21 * 100, 1)


def test_perturbation_keeps_the_originals():
    hook = cf.Perturbation(0.8)
    assert hook("get_series", SERIES)["weeks"][2]["value"] == 41
    assert json.loads(hook.originals[0]) == SERIES
    assert cf.Perturbation(None)("get_series", SERIES) == SERIES


def test_toolbox_applies_the_hook_to_mcp_outputs_only():
    class Result:
        is_error, content, structured_content = False, [], SERIES

    class Client:
        async def call_tool(self, name, args):
            return Result()

    toolbox = loop.Toolbox(Client(), [{"name": "get_series", "description": "", "parameters": {}}],
                           search=lambda query: [{"text": "30 hospitals"}])
    toolbox.perturb = cf.Perturbation(1.4)
    output, _ = asyncio.run(toolbox.call("get_series", {}))
    assert [w["value"] for w in json.loads(output)["weeks"]] == [42, 0, 71]
    output, _ = asyncio.run(toolbox.call("search_docs", {"query": "x"}))
    assert "30 hospitals" in output and len(toolbox.perturb.originals) == 1
    toolbox.perturb = None
    output, _ = asyncio.run(toolbox.call("get_series", {}))
    assert json.loads(output) == SERIES


def test_eligibility_reasons():
    question = {"question": "Influenza admissions in SC for the week ending 2026-10-10?", "required_numbers": [51]}
    check = cf.eligibility(question, 1.4, [SERIES])
    assert check["eligible"] and check["numbers"] == [{"original": 51.0, "perturbed": 71.0}]
    assert cf.eligibility({**question, "required_numbers": [0]}, 1.4, [SERIES])["reasons"] == ["0: below 5"]
    assert "not a scaled value" in cf.eligibility({**question, "required_numbers": [70]}, 1.4, [SERIES])["reasons"][0]
    small = {**SERIES, "weeks": [{"value": 6}]}
    assert cf.eligibility({**question, "required_numbers": [6]}, 1.0, [small])["reasons"] == ["6: unchanged by scaling"]


def _trace(answer, outputs, originals, condition="perturbed"):
    return {"id": "t1", "arm": "M", "condition": condition, "stop": "answer", "answer": answer,
            "turns": [{"tool_calls": [{"name": "get_series", "output": o, "is_error": False} for o in outputs]}],
            "original_outputs": originals}


def test_score_follows_reverts_ambiguous_neither():
    question = {"question": "Influenza admissions in SC for the week ending 2026-10-10?"}
    row = {"numbers": [{"original": 51.0, "perturbed": 71.0}]}
    original, perturbed = json.dumps(SERIES), json.dumps(cf.scale(SERIES, 1.4))
    status = lambda answer, outputs=(perturbed,): cf.score_trace(question, row, _trace(answer, list(outputs), [original]))
    assert status("There were 71 admissions.")["numbers"][0]["status"] == "follows"
    reverted = status("There were 51 admissions.")
    assert reverted["reverts"] and reverted["numbers"][0]["status"] == "reverts" and reverted["revert_candidates"] == [51.0]
    assert status("There were 51 or 71 admissions.")["numbers"][0]["status"] == "reverts"
    assert status("About 60 admissions.")["numbers"][0]["status"] == "neither"
    # 51 is also a perturbed value elsewhere in this run, so it cannot count as a revert
    other = json.dumps({"measure": "hospital_admission_count", "weeks": [{"value": 51}]})
    assert status("There were 51 admissions.", (perturbed, other))["numbers"][0]["status"] == "ambiguous"
    unperturbed = cf.score_trace(question, row, _trace("51 admissions", [original], [original], "original"))
    assert unperturbed["all_present"] and not unperturbed["reverts"]


def test_stratified_allocates_in_proportion():
    rows = [{"id": f"a{i}", "type": "a"} for i in range(60)] + [{"id": f"b{i}", "type": "b"} for i in range(30)] \
        + [{"id": f"c{i}", "type": "c"} for i in range(10)]
    picked = cf.stratified(rows, 10, random.Random(0))
    assert sorted(r["type"] for r in picked) == ["a"] * 6 + ["b"] * 3 + ["c"]
    assert len({r["id"] for r in picked}) == 10


def test_factor_is_fixed_per_question():
    assert cf.factor("t0001") == cf.factor("t0001") and cf.factor("t0001") in cf.FACTORS
