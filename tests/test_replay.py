import json

import pytest

from resplens.app import replay


@pytest.fixture(scope="module")
def data():
    return replay.build()


def test_replay_matches_the_reported_results(data):
    analysis = json.loads((replay.REVIEW / "analysis.json").read_text())["primary"]
    assert data["summary"]["solved"] == {s: analysis[s]["solved_tasks"] for s in replay.AGENT_SYSTEMS}
    assert len(data["tasks"]) == 24
    for system in replay.AGENT_SYSTEMS:
        runs = [run for task in data["tasks"] for run in task["runs"][system]]
        assert len(runs) == 72
        assert sum(run["success"] for run in runs) / 72 == pytest.approx(analysis[system]["mean_success"], abs=5e-4)
    assert data["summary"]["rag_correct"] == 7


def test_replay_keeps_labels_and_injections(data):
    b21 = next(task for task in data["tasks"] if task["id"] == "b21")
    outputs = [call["output"] for turn in b21["runs"]["gemma"][0]["turns"] for call in turn["tool_calls"]]
    assert any(b21["injection"]["payload"] in output for output in outputs)
    assert [run["label_source"] for run in b21["runs"]["gpt-oss"]] == ["author", "judge", "judge"]


def test_replay_stops_when_the_number_check_differs(monkeypatch):
    monkeypatch.setattr(replay, "grounding", lambda answer, question, outputs: {"direct": [], "unmatched": [-1.0]})
    with pytest.raises(replay.ReplayError, match="recomputed unmatched"):
        replay.build()


def test_replay_writes_the_site(tmp_path):
    out = replay.write(tmp_path / "site")
    assert sorted(p.name for p in out.iterdir()) == ["data.json", "index.html", "replay.css", "replay.js"]
    assert json.loads((out / "data.json").read_text())["results_url"] == replay.RESULTS_URL
