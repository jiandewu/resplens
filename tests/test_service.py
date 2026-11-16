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
        kwargs.setdefault("info", lambda model: {"digest": "sha256:fake"})
        svc = service.Service(chat_fn=chat, search=lambda query: [], log_path=tmp_path / "queries.jsonl", **kwargs)
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
    assert client.get("/api/systems").json()["other"] == {"model": "llama3.2:3b", "label": "llama3.2:3b",
                                                         "evaluated": False}
    assert "resplens agent" in client.get("/").text
    assert client.get("/static/live.js").status_code == 200


def test_b2_systems_are_offered_only_when_vllm_serves_them(make, monkeypatch):
    monkeypatch.delenv("RESPLENS_VLLM_URL", raising=False)
    _, client = make(scripted())
    assert set(client.get("/api/systems").json()) == {"gemma", "gpt-oss"}
    assert client.post("/api/ask", json={"question": QUESTION, "system": "b2-ft"}).status_code == 422
    _, client = make(scripted(), vllm_url="http://vllm", served=lambda url: {"b2-ft"})
    listed = client.get("/api/systems").json()
    assert set(listed) == {"gemma", "gpt-oss", "b2-ft"}
    assert listed["b2-ft"] == {"model": "b2-ft", "label": "Gemma 4 E4B fine-tuned (vLLM)", "evaluated": True}

    def unreachable(url):
        raise OSError("connection refused")
    _, client = make(scripted(), vllm_url="http://vllm", served=unreachable)
    assert set(client.get("/api/systems").json()) == {"gemma", "gpt-oss"}


def test_b2_system_is_sent_to_vllm_and_logged_without_a_digest(make, monkeypatch):
    replies, urls = scripted({"content": "No data."}), []

    def openai_chat(model, messages, tools, think, seed, url=None):
        urls.append((model, url))
        return replies(model, messages, tools, think, seed)

    def ollama_chat(*args):
        raise AssertionError("the b2 system must not go to Ollama")
    monkeypatch.setattr(service.loop, "openai_chat", openai_chat)
    monkeypatch.setattr(service.loop, "chat", ollama_chat)
    svc, client = make(None, vllm_url="http://vllm", served=lambda url: {"b2-ft"},
                       info=lambda model: pytest.fail("no Ollama digest for a vLLM model"))
    got = events(client.post("/api/ask", json={"question": QUESTION, "system": "b2-ft"}))
    assert got[-1]["type"] == "answer" and urls == [("b2-ft", "http://vllm")]
    line = json.loads(svc.log_path.read_text())
    assert line["backend"] == "vllm" and line["digest"] is None and line["model"] == "b2-ft"
