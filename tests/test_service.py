import json

import pytest
from fastapi.testclient import TestClient

from resplens import server
from resplens.app import service
from resplens.data import Dataset
from test_agent import SERIES, scripted, tool_call

QUESTION = "What was the most recent COVID-19 hospital admission count in ZZ?"


@pytest.fixture
def make(mirror, monkeypatch, tmp_path):
    monkeypatch.setattr(server, "_dataset", Dataset(mirror=mirror))

    def build(chat, **kwargs):
        svc = service.Service(chat_fn=chat, search=lambda query: [], log_path=tmp_path / "queries.jsonl",
                              info=lambda model: {"digest": "sha256:fake"}, **kwargs)
        return svc, TestClient(service.create_app(svc))
    return build


def events(response):
    return [json.loads(line[6:]) for line in response.text.split("\n\n") if line.startswith("data: ")]


def test_ask_streams_the_loop_and_logs_the_query(make):
    svc, client = make(scripted({"content": "", "tool_calls": [tool_call("get_series", **SERIES)]},
                                {"content": "The latest count was 65, and 123 hospitals reported."}))
    response = client.post("/api/ask", json={"question": QUESTION, "system": "gemma"})
    assert response.status_code == 200 and response.headers["content-type"].startswith("text/event-stream")
    got = events(response)
    assert [e["type"] for e in got] == ["start", "model_start", "model_turn", "tool_output", "model_start",
                                        "model_turn", "answer"]
    assert got[0]["model"] == "gemma4:31b" and got[0]["evaluated"]
    assert got[3]["name"] == "get_series" and not got[3]["is_error"] and json.loads(got[3]["output"])["weeks"][0]["value"] == 65
    assert got[-1]["direct"] == [65.0] and got[-1]["not_found"] == [123.0]
    line = json.loads((svc.log_path).read_text())
    assert line["question"] == QUESTION and line["tools"] == ["get_series"] and line["stop"] == "answer"
    assert line["digest"] == "sha256:fake" and line["numbers_not_found"] == [123.0]
    assert not svc.lock.locked()


def test_question_text_can_be_left_out_of_the_log(make):
    svc, client = make(scripted({"content": "No data."}), log_questions=False)
    client.post("/api/ask", json={"question": QUESTION, "system": "gpt-oss"})
    assert json.loads(svc.log_path.read_text())["question"] is None


def test_one_question_at_a_time(make):
    svc, client = make(scripted())
    svc.lock.acquire()
    assert client.post("/api/ask", json={"question": QUESTION}).status_code == 429


def test_question_length_and_system_are_checked(make):
    _, client = make(scripted())
    assert client.post("/api/ask", json={"question": "x" * 1001}).status_code == 422
    assert client.post("/api/ask", json={"question": "  "}).status_code == 422
    assert client.post("/api/ask", json={"question": QUESTION, "system": "other"}).status_code == 422


def test_model_failure_is_reported_and_releases_the_lock(make):
    def broken(*args):
        raise RuntimeError("model went away")
    svc, client = make(broken)
    got = events(client.post("/api/ask", json={"question": QUESTION}))
    assert got[-1] == {"type": "error", "message": "RuntimeError: model went away"}
    assert not svc.lock.locked() and not svc.log_path.exists()


def test_healthz_and_page_need_no_model(make, monkeypatch):
    monkeypatch.setenv("RESPLENS_OTHER_MODEL", "llama3.2:3b")
    _, client = make(scripted())
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/api/systems").json()["other"] == {"model": "llama3.2:3b", "evaluated": False}
    assert "resplens agent" in client.get("/").text
    assert client.get("/static/live.js").status_code == 200
