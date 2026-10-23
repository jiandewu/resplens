from resplens.retrieval.bm25 import BM25, tokenize
from resplens.retrieval.chunking import approx_tokens, chunk_document, sections
from resplens.retrieval.metrics import bootstrap_ci, first_hit_rank, mrr, recall_at


DOC = """# Methods

Intro paragraph.

## 3. Flags

### 3.2 NHSN

Admissions are flagged when the change exceeds the threshold.

```python
# not a heading
x = 1
```

Second paragraph about reporting hospitals.

## 4. Limits

Wastewater influenza covers influenza A only.
"""


def test_sections_follow_heading_levels_and_skip_code():
    found = sections(DOC)
    assert [path for path, _ in found] == [("Methods",), ("Methods", "3. Flags", "3.2 NHSN"), ("Methods", "4. Limits")]
    assert "# not a heading" in found[1][1]


def test_chunks_stay_within_sections_and_size():
    long_doc = "# A\n\n" + "\n\n".join(f"Paragraph {i} " + "word " * 60 for i in range(10)) + "\n\n# B\n\nShort."
    chunks = chunk_document("doc", long_doc, max_tokens=200, overlap=1)
    assert all(approx_tokens(chunk.text) <= 200 for chunk in chunks)
    assert chunks[-1].headings == ("B",) and chunks[-1].text == "Short."
    # one paragraph of overlap between consecutive chunks of the same section
    assert chunks[0].text.split("\n\n")[-1] == chunks[1].text.split("\n\n")[0]


def test_oversized_paragraph_is_split():
    chunks = chunk_document("doc", "# A\n\n" + "word " * 1000, max_tokens=100, overlap=0)
    assert len(chunks) > 1 and all(approx_tokens(chunk.text) <= 100 for chunk in chunks)


def test_indexed_text_prefixes_heading_path():
    chunk = chunk_document("doc", DOC)[1]
    assert chunk.indexed_text().startswith("Methods > 3. Flags > 3.2 NHSN\n")
    assert not chunk.indexed_text(with_headings=False).startswith("Methods")


def test_tokenize_keeps_identifiers():
    assert tokenize("The hospital_admission_count for COVID-19") == ["hospital_admission_count", "covid-19"]


def test_bm25_ranks_matching_document_first():
    index = BM25(["wastewater influenza A only", "hospital admissions threshold", "ED visit percent"])
    assert index.search("influenza wastewater")[0][0] == 0
    assert index.search("unrelated words") == []


def test_rank_and_metrics():
    ranked = ["nothing here", "The flag is SET when **hospitals** drop", "other"]
    assert first_hit_rank(ranked, ["the flag is set when hospitals drop"]) == 2
    assert first_hit_rank(ranked, ["flag is set", "missing quote"]) is None
    ranks = [1, 2, None, 4]
    assert recall_at(ranks, 1) == 0.25 and recall_at(ranks, 5) == 0.75
    assert mrr(ranks) == (1 + 0.5 + 0.25) / 4
    low, high = bootstrap_ci([0.0, 1.0] * 20)
    assert low < 0.5 < high


def test_long_table_is_split_between_rows():
    table = "# T\n\n" + "\n".join(f"| row {i} | " + "cell " * 20 + "|" for i in range(30))
    chunks = chunk_document("doc", table, max_tokens=120, overlap=0)
    assert len(chunks) > 1
    rows = [line for chunk in chunks for line in chunk.text.splitlines()]
    assert len(rows) == 30 and all(line.startswith("| row ") and line.endswith("|") for line in rows)


def test_check_questions_flags_bad_quotes():
    from resplens.retrieval.corpus import Document
    from resplens.retrieval.evaluate import check_questions
    doc = Document("d", 1, "all", "D", "", "# D\n\nFirst paragraph here.\n\nSecond one.")
    questions = [{"id": "ok", "evidence": [{"doc": "d", "quote": "first  PARAGRAPH"}]},
                 {"id": "missing", "evidence": [{"doc": "d", "quote": "not there"}]},
                 {"id": "span", "evidence": [{"doc": "d", "quote": "here. Second"}]},
                 {"id": "nodoc", "evidence": [{"doc": "x", "quote": "a"}]}]
    assert check_questions(questions, [doc]) == ["missing: quote not found in d",
                                                 "span: quote spans a paragraph break in d",
                                                 "nodoc: unknown document x"]


def test_corpus_files_match_manifest():
    """Raw files are stored byte for byte (see .gitattributes); a newline conversion would break this."""
    import csv
    import hashlib
    from resplens.retrieval.corpus import EXTENSIONS, ROOT
    rows = list(csv.DictReader((ROOT / "manifest.csv").open(encoding="utf-8")))
    assert rows
    for row in rows:
        raw = (ROOT / "raw" / f"{row['id']}.{EXTENSIONS[row['kind']]}").read_bytes()
        text = (ROOT / "text" / f"{row['id']}.md").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["raw_sha256"], row["id"]
        assert hashlib.sha256(text).hexdigest() == row["text_sha256"], row["id"]


def test_split_table_repeats_header_in_every_piece():
    header = "| State | Low | High |\n|---|---|---|"
    rows = "\n".join(f"| S{i} | " + "x " * 15 + f"| {i} |" for i in range(40))
    chunks = chunk_document("doc", "# T\n\n" + header + "\n" + rows, max_tokens=150, overlap=0)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.text.startswith(header) and approx_tokens(chunk.text) <= 150
    body = [line for chunk in chunks for line in chunk.text.splitlines()[2:]]
    assert len(body) == 40


def test_rrf_rewards_agreement_between_rankings():
    from resplens.retrieval.dense import rrf
    assert rrf([[1, 2, 3], [3, 1, 4]], k=3) == [1, 3, 2]
    assert rrf([[5], []], k=2) == [5]


def test_heading_path_counts_toward_the_budget():
    long_heading = "# " + "Heading " * 30
    chunks = chunk_document("doc", long_heading + "\n\n" + "\n\n".join("word " * 20 for _ in range(10)),
                            max_tokens=120, overlap=0)
    assert all(approx_tokens(chunk.indexed_text()) <= 120 + 2 for chunk in chunks)


def test_untracked_inputs_mark_a_run_dirty(tmp_path):
    """Runs once recorded a clean commit while a new, uncommitted module produced them."""
    import subprocess
    from resplens.retrieval.evaluate import _git_commit

    def git(*args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=tmp_path, check=True,
                       capture_output=True)

    git("init", "-q")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    git("add", "src")
    git("commit", "-q", "-m", "init")
    assert not _git_commit(tmp_path).endswith("-dirty")
    (tmp_path / "eval" / "runs" / "r").mkdir(parents=True)
    (tmp_path / "eval" / "runs" / "r" / "summary.json").write_text("{}")
    assert not _git_commit(tmp_path).endswith("-dirty")
    (tmp_path / "src" / "new.py").write_text("y = 2\n")
    assert _git_commit(tmp_path).endswith("-dirty")
