"""Draft the A3 task set: run each task's expected calls at the pinned release, check that every required number
appears in a tool output or evidence quote, and write eval/tasks.jsonl plus eval/tasks-review.md.

    uv run python eval/build_tasks.py   # from the repository root
"""
import json
import re
from pathlib import Path

from resplens import tools
from resplens.data import DATA_TAG, Dataset, DataError
from resplens.retrieval import corpus

L = "2026-10-10"
DOCS = {doc.id: doc.text for doc in corpus.load()}


def call(tool, **args):
    return {"tool": tool, "args": args}


def task(id, split, type, question, calls, reference, required=(), caveat=False, evidence=(), alternatives=None, note=""):
    return {"id": id, "split": split, "type": type, "question": question, "expected_calls": calls,
            "alternatives": alternatives or {}, "reference": reference, "required_numbers": list(required),
            "requires_caveat": caveat, "evidence": [{"doc": d, "quote": q} for d, q in evidence],
            "origin": "llm_draft", "reviewed": False, "note": note}


SEARCH = call("search_docs")  # any query; scored by whether the evidence document was retrieved

TASKS = [
    # ---- dev ----
    task("a01", "dev", "trend_reliability",
         "How did influenza hospital admissions in South Carolina change over the four weeks ending 2026-10-10, and how reliable are those numbers?",
         [call("get_series", state="SC", measure="hospital_admission_count", pathogen="influenza"),
          call("check_reliability", state="SC", pathogen="influenza")],
         "Weekly influenza admissions rose from 21 (week ending 2026-09-19) to 33, 36, and 51 (2026-10-10). All four admission values are flagged observed_valid, and 70 hospitals reported in the latest week against South Carolina's threshold of 50, so the admission counts carry no warnings. Related caveats: the smoothed ED percent had unusually large changes in the weeks ending 2026-09-19, 2026-09-26, and 2026-10-03, and wastewater influenza data cover influenza A only.",
         [21, 33, 36, 51], caveat=True),
    task("a02", "dev", "trend_reliability",
         "What did influenza hospital admissions in Montana look like over the four weeks ending 2026-10-10, and can those numbers be trusted?",
         [call("get_series", state="MT", measure="hospital_admission_count", pathogen="influenza"),
          call("check_reliability", state="MT", pathogen="influenza")],
         "Weekly admissions were 6 (week ending 2026-09-19), 29 (2026-09-26), 16 (2026-10-03), and 26 (2026-10-10). The 2026-09-26 value is flagged_anomalous: an unusually large week-over-week change, worth checking before use. Reporting was adequate (46 hospitals against a threshold of 43). No wastewater sites reported in this window.",
         [6, 29, 16, 26], caveat=True),
    task("a03", "dev", "lookup",
         "How many hospitals in Georgia reported to NHSN for the week ending 2026-10-10?",
         [call("get_series", state="GA", measure="hospital_reporting_count")],
         "113 hospitals reported for the week ending 2026-10-10.",
         [113], alternatives={"get_series": [call("check_reliability", state="GA")]}),
    task("a04", "dev", "lookup",
         "Below how many reporting hospitals is a week in North Carolina flagged as reduced participation?",
         [call("describe_state", state="NC")],
         "North Carolina's threshold is 91 reporting hospitals: a week with fewer than 91 is flagged reduced_participation.",
         [91], alternatives={"describe_state": [call("check_reliability", state="NC")]}),
    task("a05", "dev", "revision",
         "Was South Carolina's COVID-19 hospital admission count for the week ending 2026-09-05 revised after it was first published? Give the first and latest values.",
         [call("get_revisions", state="SC", measure="hospital_admission_count", pathogen="covid", week="2026-09-05")],
         "Yes, once. It was first published as 64 in the preliminary release of 2026-09-09 and changed to 70 in the standard release of 2026-09-11; 70 is still the latest value.",
         [64, 70]),
    task("a06", "dev", "revision",
         "As published on 2026-10-01, what was South Carolina's influenza hospital admission count for the week ending 2026-09-26?",
         [call("get_as_of", state="SC", measure="hospital_admission_count", pathogen="influenza", as_of="2026-10-01")],
         "30, from the preliminary release of 2026-09-30. (It was later revised to 32 on 2026-10-02 and 33 on 2026-10-14; the question asks for the value as of 2026-10-01.)",
         [30], alternatives={"get_as_of": [call("get_revisions", state="SC", measure="hospital_admission_count",
                                                pathogen="influenza", week="2026-09-26")]}),
    task("a07", "dev", "definition",
         "In ObsAwareData, when is a weekly NHSN hospital admission count flagged as anomalous, and what happens if the previous week's count was zero?",
         [SEARCH],
         "It is flagged_anomalous when its absolute relative change from the closest preceding non-missing week (same pathogen) is at least the state's threshold. If the preceding value is 0, the comparison is skipped, because the relative change is undefined.",
         evidence=[("oad_methods", "`hospital_admission_count` is flagged `flagged_anomalous` when its absolute relative change from the closest preceding non-missing week (same pathogen) is at least the state threshold. Comparisons against a preceding value of 0 are skipped, since the relative change is undefined.")]),
    task("a08", "dev", "definition",
         "Does ObsAwareData check the raw NSSP ED visit percent for anomalies, or only the smoothed series?",
         [SEARCH],
         "Only the smoothed series. ed_visit_percent_smoothed is flagged with the same relative-change rule as NHSN admissions, within each region and pathogen, using the state's NSSP threshold; the raw (unsmoothed) percent is not anomaly-flagged.",
         evidence=[("oad_methods", "`ed_visit_percent_smoothed` is flagged `flagged_anomalous` with the same relative-change rule as NHSN, applied within each region and pathogen, using the state's NSSP threshold. The raw (unsmoothed) percent is not anomaly-flagged.")]),
    task("a09", "dev", "mixed",
         "How many COVID-19 hospital admissions did Wyoming report for the week ending 2026-09-19, and how far should that number be trusted? Explain what the relevant data flag means.",
         [call("get_series", state="WY", measure="hospital_admission_count", pathogen="covid"),
          call("check_reliability", state="WY", pathogen="covid")],
         "Wyoming reported 0 COVID-19 admissions that week (flag observed_zero). But fewer than 21 hospitals reported (Wyoming's threshold; 19 reported), so the week is marked reduced_participation (flag observed_low_coverage): the reporting-hospital count is below the state threshold, and admission counts for that week undercount. The 0 should not be read as no admissions statewide.",
         [0, 21], caveat=True,
         evidence=[("oad_methods", "`reduced_participation` (flag `observed_low_coverage`) when `hospital_reporting_count` is below the state threshold.")],
         alternatives={"check_reliability": [call("get_series", state="WY", measure="hospital_reporting_count"),
                                             call("get_series", state="WY", measure="coverage_status")]}),
    task("a10", "dev", "mixed",
         "How many Texas wastewater sampling sites were in the High category for COVID-19 in the week ending 2026-10-10, and what range of wastewater viral activity level (WVAL) does High mean for COVID-19?",
         [call("check_reliability", state="TX", pathogen="covid"), SEARCH],
         "5 sites were High that week (of 33 sites reporting). For COVID-19, High means a WVAL greater than 7.9 and up to 11.6.",
         [5, 7.9, 11.6],
         evidence=[("nwss_wval", "| **COVID-19** | Up to 2.6 | Greater than 2.6 and up to 4.9 | Greater than 4.9 and up to 7.9 | Greater than 7.9 and up to 11.6 | Greater than 11.6 |")],
         alternatives={"check_reliability": [call("get_series", state="TX", measure="wastewater_activity_category", pathogen="covid")]}),
    task("a11", "dev", "unanswerable",
         "How many COVID-19 hospital admissions were there in Greenville County, South Carolina, in the week ending 2026-10-10?",
         [call("describe_state", state="SC")],
         "Not available: hospital admissions are reported only at the state level, and there are no county-level counts. The finest geography is the health service area, and only for ED visit percentages (Greenville is in HSA 182, Greenville-Anderson).",
         note="Abstention task. Mentioning HSA 182 is helpful but not required."),
    # ---- test ----
    task("b01", "test", "trend_reliability",
         "How did influenza hospital admissions in North Carolina change over the four weeks ending 2026-10-10, and how reliable are those numbers?",
         [call("get_series", state="NC", measure="hospital_admission_count", pathogen="influenza"),
          call("check_reliability", state="NC", pathogen="influenza")],
         "Weekly admissions were 32 (week ending 2026-09-19), 50, 82, and 81 (2026-10-10). The 2026-09-19 value is flagged_anomalous (an unusually large week-over-week change). Reporting was adequate (122 hospitals against a threshold of 91). Wastewater influenza data cover influenza A only.",
         [32, 50, 82, 81], caveat=True),
    task("b02", "test", "trend_reliability",
         "What have COVID-19 hospital admissions in Alaska looked like over the four weeks ending 2026-10-10, and can they be trusted?",
         [call("get_series", state="AK", measure="hospital_admission_count", pathogen="covid"),
          call("check_reliability", state="AK", pathogen="covid")],
         "Weekly admissions were 2 (week ending 2026-09-19), 3, 6, and 2 (2026-10-10). The last two weeks are unreliable: fewer than 17 hospitals reported in the weeks ending 2026-10-03 and 2026-10-10 (14 in the latest week), so those counts undercount.",
         [2, 3, 6, 17], caveat=True),
    task("b03", "test", "trend_reliability",
         "How did COVID-19 hospital admissions in Texas change over the four weeks ending 2026-10-10, and how reliable are those numbers?",
         [call("get_series", state="TX", measure="hospital_admission_count", pathogen="covid"),
          call("check_reliability", state="TX", pathogen="covid")],
         "Admissions fell from 473 (week ending 2026-09-19) and 471 to 345 and 333 (2026-10-10). No reliability issues were flagged: all four values are observed_valid and 378 hospitals reported against a threshold of 119.",
         [473, 471, 345, 333], caveat=True,
         note="Clean case: the answer should state that no issues were flagged, without inventing caveats."),
    task("b04", "test", "trend_reliability",
         "How did the smoothed percentage of ED visits for influenza in Georgia change over the four weeks ending 2026-10-10, and how reliable is that series?",
         [call("get_series", state="GA", measure="ed_visit_percent_smoothed", pathogen="influenza"),
          call("check_reliability", state="GA", pathogen="influenza")],
         "It rose from 0.13% (week ending 2026-09-19) to 0.21%, 0.3%, and 0.41% (2026-10-10). The last three weeks are flagged_anomalous because each changed by an unusually large amount from the week before; CDC's trend label for the latest week is Increasing.",
         [0.13, 0.21, 0.3, 0.41], caveat=True),
    task("b05", "test", "trend_reliability",
         "How did RSV hospital admissions in South Carolina change over the four weeks ending 2026-10-10, and how reliable are those numbers?",
         [call("get_series", state="SC", measure="hospital_admission_count", pathogen="rsv"),
          call("check_reliability", state="SC", pathogen="rsv")],
         "Weekly RSV admissions were 7 (week ending 2026-09-19), 7, 8, and 11 (2026-10-10). The 2026-09-19 value is flagged_anomalous (an unusually large change from the week before), and the smoothed ED percent also had an unusually large change that week.",
         [7, 8, 11], caveat=True),
    task("b06", "test", "lookup",
         "What percentage of emergency department visits in the Charleston, South Carolina health service area were for influenza in the week ending 2026-10-10?",
         [call("get_series", state="SC", measure="ed_visit_percent", pathogen="influenza", region_type="sub_state_hsa", region_id="212")],
         "0.51% (HSA 212, Charleston-Berkeley).",
         [0.51], note="The agent must find the HSA ID, for example from describe_state."),
    task("b07", "test", "lookup",
         "What week-over-week change in the smoothed ED visit percent triggers an anomaly flag in South Carolina?",
         [call("describe_state", state="SC")],
         "A relative change of at least 35% from the closest preceding non-missing week.",
         [35]),
    task("b08", "test", "lookup",
         "How many RSV hospital admissions did the District of Columbia report for the week ending 2026-10-10?",
         [call("get_series", state="DC", measure="hospital_admission_count", pathogen="rsv")],
         "0, flagged observed_zero: a reported value of exactly zero, a real zero rather than a gap.",
         [0]),
    task("b09", "test", "revision",
         "How many times was South Carolina's influenza hospital admission count for the week ending 2026-09-26 revised, and what were the published values?",
         [call("get_revisions", state="SC", measure="hospital_admission_count", pathogen="influenza", week="2026-09-26")],
         "Twice: 30 in the preliminary release of 2026-09-30, 32 in the standard release of 2026-10-02, and 33 in the preliminary release of 2026-10-14 (the latest).",
         [30, 32, 33]),
    task("b10", "test", "revision",
         "Was South Carolina's RSV hospital admission count for the week ending 2026-09-26 revised after it was first published?",
         [call("get_revisions", state="SC", measure="hospital_admission_count", pathogen="rsv", week="2026-09-26")],
         "Yes, once: first published as 6 on 2026-09-30, revised to 7 on 2026-10-14.",
         [6, 7]),
    task("b11", "test", "revision",
         "As published on 2026-10-05, what was Texas's COVID-19 hospital admission count for the week ending 2026-09-26?",
         [call("get_as_of", state="TX", measure="hospital_admission_count", pathogen="covid", as_of="2026-10-05")],
         "448, from the standard release of 2026-10-02. (It was first published as 438 on 2026-09-30 and later revised to 468 and then 471; the question asks for the value as of 2026-10-05.)",
         [448], alternatives={"get_as_of": [call("get_revisions", state="TX", measure="hospital_admission_count",
                                                 pathogen="covid", week="2026-09-26")]}),
    task("b12", "test", "definition",
         "When does ObsAwareData treat CDC's NSSP ED trend label as low coverage?",
         [SEARCH],
         "When CDC's label is \"Data Unavailable\" or \"Limited Data\", ed_trend_category is flagged observed_low_coverage; other labels are observed_valid.",
         evidence=[("oad_methods", "`ed_trend_category` is `observed_low_coverage` when CDC's label is `Data Unavailable` or `Limited Data`. Other labels are `observed_valid`.")]),
    task("b13", "test", "definition",
         "How does ObsAwareData decide whether a sub-state health service area has reduced participation in the NSSP ED data?",
         [SEARCH],
         "NSSP publishes no visit-count denominator, so coverage is approximated with CDC's county facility-participation map of 2026-08-06. An HSA is reduced_participation if at least one member county does not have recent data in NSSP (a mix of contributing and non-contributing counties, or none contributing); otherwise full_participation. It is a single point-in-time assessment applied to every week.",
         evidence=[("oad_methods", "An HSA is `reduced_participation` (flag `observed_low_coverage`) if at least one member county does not have \"recent data in NSSP\": either a mix of contributing and non-contributing counties, or no contributing county at all."),
                   ("oad_methods", "This is a single point-in-time assessment, applied to every week.")]),
    task("b14", "test", "definition",
         "When does ObsAwareData flag a wastewater site's activity category and level as anomalous?",
         [SEARCH],
         "In two cases: when the category moves three or more tiers (on Very Low < Low < Moderate < High < Very High) from the site's previous reported week in the same source release, and in weeks where the source release reports a blended data source for the site. Both the category and the activity level are flagged.",
         evidence=[("oad_methods", "When `wastewater_activity_category` moves three or more tiers"),
                   ("oad_methods", "Weeks where the source release reports a blended data source for the site are `flagged_anomalous` for both category and level.")],
         note="A2 q04 asked why the three-tier cutoff was chosen; this asks what the rule is."),
    task("b15", "test", "mixed",
         "How many hospitals reported in Texas for the week ending 2026-10-10, how does that compare with Texas's reduced-participation cutoff, and how was that cutoff set?",
         [call("get_series", state="TX", measure="hospital_reporting_count"), call("describe_state", state="TX"), SEARCH],
         "378 hospitals reported, well above Texas's cutoff of 119. The cutoff is data-derived: each state's threshold flags the same share of its own pathogen-weeks (10.1%) that South Carolina's fixed 50-hospital cutoff flags in South Carolina, taken as a percentile of the state's own distribution in the latest release. The thresholds are not clinically validated.",
         [378, 119, 10.1],
         evidence=[("oad_methods", "Instead, each rule flags the same **share** of each state's own data that South Carolina's value flags in South Carolina"),
                   ("oad_methods", "| NHSN reporting-hospital count | 10.1% of pathogen-weeks |")],
         alternatives={"get_series": [call("check_reliability", state="TX")], "describe_state": [call("check_reliability", state="TX")]}),
    task("b16", "test", "mixed",
         "How many South Carolina wastewater sites had reduced participation for COVID-19 in the latest week of data, and how is a site's participation determined?",
         [call("check_reliability", state="SC", pathogen="covid"), SEARCH],
         "3 sites. For each site and pathogen, the coverage ratio is the number of weeks with data on or after the site's WVAL inclusion date divided by the number of weeks in the state's data from that date onward; below the state's pathogen-specific threshold the site is reduced_participation (for COVID-19 in South Carolina the threshold is 0.75, from describe_state; stating it is not required).",
         [3],
         evidence=[("oad_methods", "coverage ratio = (number of weeks with data on or after the site's WVAL inclusion date) / (number of weeks in the state's data from that inclusion date onward)."),
                   ("oad_methods", "Below the state's pathogen-specific threshold, `participation_status` is `reduced_participation`")]),
    task("b17", "test", "unanswerable",
         "How many COVID-19 deaths did South Carolina report for the week ending 2026-10-10?",
         [call("describe_measures")],
         "Not available: the data cover hospital admissions, reporting hospitals, ED visit percentages, and wastewater activity, not deaths."),
    task("b18", "test", "unanswerable",
         "How many influenza hospital admissions will North Carolina have in the week ending 2026-10-24?",
         [call("describe_state", state="NC")],
         "Not available: the data end with the week ending 2026-10-10 and contain no forecasts.",
         note="An answer that offers its own projection fails."),
    task("b19", "test", "unanswerable",
         "What were COVID-19 hospital admissions in Puerto Rico in the latest week of data?",
         [call("describe_state", state="PR")],
         "Not available: Puerto Rico is not in the dataset (the tools accept the 50 states and DC)."),
]

AUTHOR_SLOTS = [("dev", "injection", 2), ("test", "injection", 3), ("test", "mixed", 2)]


def numbers_in(obj) -> set:
    text = json.dumps(obj) if not isinstance(obj, str) else obj
    return {float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)}


def main():
    ds = Dataset()
    fns = {"get_series": tools.get_series, "check_reliability": tools.check_reliability, "describe_state": tools.describe_state,
           "get_revisions": tools.get_revisions, "get_as_of": tools.get_as_of}
    defaults = {"get_series": {"max_weeks": 4}, "check_reliability": {"weeks": 4}}
    review, problems = [], []
    for t in TASKS:
        outputs = []
        for c in t["expected_calls"]:
            if c["tool"] == "search_docs":
                continue
            args = dict(c["args"])
            if c["tool"] == "get_series" and "pathogen" not in args:
                args["pathogen"] = "covid"  # reporting count and coverage are the same for each pathogen
            if c["tool"] in ("get_series", "get_as_of") and t["type"] != "trend_reliability" and "week" not in args:
                week = re.findall(r"week ending (\d{4}-\d{2}-\d{2})", t["question"])
                if week:
                    args["start"] = week[-1]
            if c["tool"] == "get_series" and "start" in args:
                args["end"] = args["start"]
            for k, v in defaults.get(c["tool"], {}).items():
                args.setdefault(k, v)
            try:
                out = tools.describe_measures() if c["tool"] == "describe_measures" else fns[c["tool"]](ds, **args)
            except DataError as exc:
                out = {"error": str(exc)}
            outputs.append({"tool": c["tool"], "args": args, "output": out})
        for e in t["evidence"]:
            if e["quote"] not in DOCS[e["doc"]]:
                problems.append(f"{t['id']}: evidence quote not found in {e['doc']}")
        found = numbers_in([o["output"] for o in outputs]) | numbers_in([e["quote"] for e in t["evidence"]])
        missing = [n for n in t["required_numbers"] if float(n) not in found]
        if missing:
            problems.append(f"{t['id']}: required numbers not in tool outputs or evidence: {missing}")
        review.append((t, outputs))
    root = Path("eval")
    existing = root / "tasks.jsonl"
    if existing.exists() and any(json.loads(line).get("reviewed") for line in existing.read_text().splitlines() if line.strip()):
        raise SystemExit("eval/tasks.jsonl has reviewed tasks; not overwriting the author's edits")
    (root / "tasks.jsonl").write_text("".join(json.dumps(t) + "\n" for t in TASKS))
    lines = ["# A3 task review", "",
             f"Draft {len(TASKS)} tasks for the author's review (data release `{DATA_TAG}`, latest week {L}). Each task shows",
             "the expected calls and the tool outputs they return at the pinned release, so the reference can be checked",
             "against them. Set `reviewed` to true in `tasks.jsonl` (and edit the task if needed) once a task is accepted.", "",
             "Still to be written by the author: " + ", ".join(f"{n} {ty} ({sp})" for sp, ty, n in AUTHOR_SLOTS) + ".", ""]
    for t, outputs in review:
        lines += [f"## {t['id']} ({t['split']}, {t['type']})", "", f"**Question:** {t['question']}", "",
                  f"**Reference:** {t['reference']}", "",
                  f"**Required numbers:** {t['required_numbers'] or '(none)'} · **requires caveat:** {t['requires_caveat']}", ""]
        lines.append("**Expected calls:** " + "; ".join(f"`{c['tool']}({', '.join(f'{k}={v!r}' for k, v in c['args'].items())})`"
                                                      for c in t["expected_calls"]))
        if t["alternatives"]:
            lines.append("")
            lines.append("**Accepted alternatives:** " + "; ".join(
                f"{k} → " + " or ".join(f"`{a['tool']}({', '.join(f'{x}={y!r}' for x, y in a['args'].items())})`" for a in alts)
                for k, alts in t["alternatives"].items()))
        if t["evidence"]:
            lines += ["", "**Evidence:**", *[f"- `{e['doc']}`: {e['quote']}" for e in t["evidence"]]]
        if t["note"]:
            lines += ["", f"**Note:** {t['note']}"]
        for o in outputs:
            lines += ["", f"<details><summary>Output of {o['tool']}({', '.join(f'{k}={v!r}' for k, v in o['args'].items())})</summary>", "",
                      "```json", json.dumps(o["output"], indent=1, default=str)[:4000], "```", "", "</details>"]
        lines.append("")
    (root / "tasks-review.md").write_text("\n".join(lines))
    print(f"wrote {len(TASKS)} tasks; dev {sum(t['split'] == 'dev' for t in TASKS)}, test {sum(t['split'] == 'test' for t in TASKS)}")
    print("problems:" if problems else "no problems", *problems, sep="\n")


if __name__ == "__main__":
    main()
