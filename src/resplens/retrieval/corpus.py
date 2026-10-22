"""Build the A2 document corpus: download sources unchanged, extract text, record provenance.

    uv run --extra corpus python -m resplens.retrieval.corpus          # fetch missing, re-extract all
    uv run --extra corpus python -m resplens.retrieval.corpus --refresh  # fetch everything again

Raw files go to corpus/raw/ exactly as served; extracted Markdown goes to corpus/text/.
corpus/manifest.csv records the URL, retrieval date, and SHA-256 of every raw and text file.
CDC material is public domain (https://www.cdc.gov/other/agencymaterials.html); ObsAwareData
documentation is CC BY 4.0.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from ..data import DATA_TAG, REPO


ROOT = Path(__file__).resolve().parents[3] / "corpus"
EXTENSIONS = {"html": "html", "pdf": "pdf", "socrata": "json", "socrata_description": "json", "markdown": "md", "obsawaredata": "md"}
MANIFEST_COLUMNS = ["id", "tier", "system", "kind", "title", "url", "retrieved", "raw_bytes", "raw_sha256",
                    "text_words", "text_sha256"]
USER_AGENT = "resplens corpus builder (+https://github.com/jiandewu/resplens)"


@dataclass(frozen=True)
class Document:
    id: str
    tier: int
    system: str
    title: str
    url: str
    text: str


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _source_url(row: dict) -> str:
    if row["kind"] == "obsawaredata":
        return f"https://raw.githubusercontent.com/{REPO}/{urllib.parse.quote(DATA_TAG, safe='')}/{row['url']}"
    return row["url"]


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


# -- extraction ---------------------------------------------------------------

class _TableParser(HTMLParser):
    """Collect <table> elements as (caption, rows of cell text)."""

    def __init__(self):
        super().__init__()
        self.tables: list[tuple[str, list[list[str]]]] = []
        self._rows: list[list[str]] | None = None
        self._cell: list[str] | None = None
        self._caption: list[str] | None = None
        self._caption_text = ""

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._rows, self._caption_text = [], ""
        elif tag == "caption" and self._rows is not None:
            self._caption = []
        elif tag == "tr" and self._rows is not None:
            self._rows.append([])
        elif tag in ("td", "th") and self._rows is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._rows:
            self._rows[-1].append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "caption" and self._caption is not None:
            self._caption_text = " ".join("".join(self._caption).split())
            self._caption = None
        elif tag == "table" and self._rows is not None:
            self.tables.append((self._caption_text, [row for row in self._rows if any(row)]))
            self._rows = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)
        elif self._caption is not None:
            self._caption.append(data)


def html_tables(html: str) -> str:
    """Every <table> as a Markdown table, each under its caption."""
    parser = _TableParser()
    parser.feed(html)
    blocks = []
    for caption, rows in parser.tables:
        if len(rows) < 2:
            continue
        width = max(len(row) for row in rows)
        rows = [row + [""] * (width - len(row)) for row in rows]
        lines = ["| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |" for row in rows]
        lines.insert(1, "|" + "---|" * width)
        blocks.append((f"### {caption}\n\n" if caption else "") + "\n".join(lines))
    return "\n\n".join(blocks)


def extract_html(raw: bytes) -> str:
    import trafilatura

    html = raw.decode("utf-8", "replace")
    text = trafilatura.extract(html, output_format="markdown", include_tables=True, include_links=False,
                               include_images=False, include_comments=False) or ""
    # trafilatura drops some data tables as page furniture; keep them when it does.
    if "<table" in html and "\n|" not in text and (tables := html_tables(html)):
        text += "\n\n## Tables\n\n" + tables
    return text


def extract_pdf(raw: bytes) -> str:
    from pypdf import PdfReader

    pages = [page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages]
    return "\n\n".join(re.sub(r"[ \t]+\n", "\n", page).strip() for page in pages if page.strip())


def html_to_text(fragment: str) -> str:
    """Plain text from the small HTML fragments in Socrata descriptions; list items on their own lines."""
    text = re.sub(r"(?i)<\s*li[^>]*>", "\n- ", fragment)
    text = re.sub(r"(?i)<\s*(br|/p|/ul|/ol|/li|/h\d|p|ul|ol|h\d)[^>]*>", "\n", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def extract_socrata(raw: bytes, columns: bool = True) -> str:
    """Dataset description and one section per documented column, from the Socrata metadata API."""
    meta = json.loads(raw)
    lines = [html_to_text(meta.get("description", ""))]
    if not columns:
        return lines[0]
    lines += ["", "## Columns"]
    for column in meta.get("columns", []):
        if column.get("fieldName", "").startswith(":"):
            continue  # Socrata system columns
        lines += ["", f"### {column.get('name', '')} (`{column.get('fieldName', '')}`)", ""]
        lines.append(html_to_text(column.get("description", "")) or "No description provided.")
    return "\n".join(lines)


EXTRACTORS = {"html": extract_html, "pdf": extract_pdf, "socrata": extract_socrata,
              # a dataset whose column dictionary repeats another dataset's: description only
              "socrata_description": lambda raw: extract_socrata(raw, columns=False),
              "markdown": lambda raw: raw.decode("utf-8"), "obsawaredata": lambda raw: raw.decode("utf-8")}


def _strip_leading_title(text: str) -> str:
    """Drop a first-line H1 so every text file starts with the same title line from sources.csv."""
    lines = text.lstrip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


# -- build ----------------------------------------------------------------------

def build(root: Path = ROOT, refresh: bool = False, log=print) -> list[dict]:
    sources = _read_csv(root / "sources.csv")
    previous = {row["id"]: row for row in _read_csv(root / "manifest.csv")}
    manifest = []
    for source in sources:
        raw_path = root / "raw" / f"{source['id']}.{EXTENSIONS[source['kind']]}"
        retrieved = previous.get(source["id"], {}).get("retrieved", "")
        if refresh or not raw_path.exists():
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                raw_path.write_bytes(download(_source_url(source)))
            except Exception as exc:  # one failed source must not stop the build
                log(f"FAILED {source['id']}: {type(exc).__name__}: {exc}")
                continue
            retrieved = date.today().isoformat()
        raw = raw_path.read_bytes()
        body = _strip_leading_title(EXTRACTORS[source["kind"]](raw))
        if len(body.split()) < 50:
            log(f"WARNING {source['id']}: only {len(body.split())} words extracted")
        text = f"# {source['title']}\n\n{body}\n"
        text_path = root / "text" / f"{source['id']}.md"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(text, encoding="utf-8")
        manifest.append({**{key: source[key] for key in ("id", "tier", "system", "kind", "title")},
                         "url": _source_url(source), "retrieved": retrieved, "raw_bytes": len(raw),
                         "raw_sha256": hashlib.sha256(raw).hexdigest(), "text_words": len(text.split()),
                         "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})
        log(f"{source['id']}: {len(text.split())} words")
    with (root / "manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest)
    return manifest


def load(root: Path = ROOT, tiers: tuple[int, ...] = (1, 2)) -> list[Document]:
    """Documents listed in the manifest, after checking each text file's SHA-256."""
    documents = []
    for row in _read_csv(root / "manifest.csv"):
        if int(row["tier"]) not in tiers:
            continue
        text = (root / "text" / f"{row['id']}.md").read_text(encoding="utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != row["text_sha256"]:
            raise ValueError(f"corpus/text/{row['id']}.md does not match the manifest; rebuild the corpus")
        documents.append(Document(row["id"], int(row["tier"]), row["system"], row["title"], row["url"], text))
    return documents


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--refresh", action="store_true", help="download every source again")
    args = parser.parse_args(argv)
    manifest = build(refresh=args.refresh)
    print(f"{len(manifest)} documents, {sum(int(row['text_words']) for row in manifest)} words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
