import json

from resplens.retrieval.answer import cited_documents, format_documents
from resplens.retrieval.judge import _sign_test, agreement


def test_cited_documents_parses_last_line():
    answer = "Thresholds come from NHSN.\nSources: nhsn_hrd_methods, `resp_faq`."
    assert cited_documents(answer) == ["nhsn_hrd_methods", "resp_faq"]
    assert cited_documents("No sources line here.") == []


def test_format_documents_wraps_ids():
    assert format_documents([("a", "text")]) == "<document id='a'>\ntext\n</document>"


def test_sign_test():
    assert _sign_test(8, 0) == 2 / 2 ** 8
    assert _sign_test(0, 0) == 1.0


def test_agreement_reads_sheet_and_computes_kappa(tmp_path):
    (tmp_path / "human-key.jsonl").write_text(
        "".join(json.dumps({"sheet_id": f"H0{i}", "id": f"q{i}", "system": "rag"}) + "\n" for i in (1, 2, 3, 4)))
    labels = ["correct", "incorrect", "correct", "partial"]
    (tmp_path / "human-review.md").write_text("\n".join(
        f"## H0{i}\n\n**correctness:** {label}\n" for i, label in zip((1, 2, 3, 4), labels)))
    judged = {(f"q{i}", "rag"): {"correctness": label} for i, label in zip((1, 2, 3, 4), labels)}
    judged[("q4", "rag")] = {"correctness": "correct"}
    result = agreement(tmp_path, judged)
    assert result["scored"] == 4 and result["agreement"] == 0.75
    assert result["disagreements"] == [("H04", "partial", "correct")]
    assert 0 < result["cohen_kappa"] < 1


class _Response:
    def __init__(self, body: dict):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, *args):
        return self.body


def test_chat_refuses_truncation_and_full_windows(monkeypatch):
    import io
    import urllib.error

    import pytest

    from resplens.retrieval import answer

    sent = []

    def reply(body):
        def urlopen(request, timeout):
            sent.append(json.loads(request.data))
            if isinstance(body, Exception):
                raise body
            return _Response(body)
        monkeypatch.setattr(answer.urllib.request, "urlopen", urlopen)

    reply({"message": {"content": "ok"}, "prompt_eval_count": 100, "eval_count": 20, "done_reason": "stop"})
    assert answer.chat([], num_ctx=4096)["message"]["content"] == "ok"
    assert sent[-1]["truncate"] is False and sent[-1]["shift"] is False

    error = '{"error":"request (8905 tokens) exceeds the available context size (4096 tokens), try increasing it"}'
    reply(urllib.error.HTTPError("url", 400, "Bad Request", {}, io.BytesIO(error.encode())))
    with pytest.raises(answer.ContextOverflow, match="8905 tokens"):
        answer.chat([], num_ctx=4096)

    reply({"message": {"content": "cut"}, "prompt_eval_count": 3000, "eval_count": 1000, "done_reason": "length"})
    with pytest.raises(answer.ContextOverflow, match="window full"):
        answer.chat([], num_ctx=4096)

    reply({"message": {"content": "x"}, "prompt_eval_count": 3500, "eval_count": 20, "done_reason": "stop"})
    with pytest.raises(answer.ContextOverflow, match="exceeds num_ctx"):
        answer.chat([], num_ctx=4096)
