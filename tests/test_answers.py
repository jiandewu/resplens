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
