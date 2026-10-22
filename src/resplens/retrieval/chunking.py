"""Split Markdown documents into retrieval chunks, keeping each chunk inside one section."""

from __future__ import annotations

import re
from dataclasses import dataclass


HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
WORD = re.compile(r"\S+")


@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    headings: tuple[str, ...]
    text: str

    def indexed_text(self, with_headings: bool = True) -> str:
        """Text used for indexing; the heading path gives short chunks their context."""
        if with_headings and self.headings:
            return " > ".join(self.headings) + "\n" + self.text
        return self.text


def approx_tokens(text: str) -> int:
    """About 1.3 tokens per English word; exact counts depend on the tokenizer."""
    return round(len(WORD.findall(text)) * 1.3)


def sections(markdown: str) -> list[tuple[tuple[str, ...], str]]:
    """(heading path, body) for every section; text before the first heading has an empty path."""
    path: list[tuple[int, str]] = []
    result, body = [], []
    in_code = False

    def flush():
        text = "\n".join(body).strip()
        if text:
            result.append((tuple(title for _, title in path), text))
        body.clear()

    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        match = None if in_code else HEADING.match(line)
        if match:
            flush()
            level = len(match.group(1))
            path = [(lvl, title) for lvl, title in path if lvl < level] + [(level, match.group(2))]
        else:
            body.append(line)
    flush()
    return result


def _paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


TABLE_SEPARATOR = re.compile(r"^\|(\s*:?-+:?\s*\|)+\s*$")


def _split_long(paragraph: str, max_tokens: int, count=approx_tokens) -> list[str]:
    """Split one oversized paragraph at line breaks (keeping table rows whole), else at words.

    A Markdown table keeps its header row and separator at the top of every piece, so a
    row retrieved on its own still says what its columns mean.
    """
    lines = paragraph.splitlines()
    if len(lines) > 2 and lines[0].startswith("|") and TABLE_SEPARATOR.match(lines[1]):
        header = lines[:2]
        budget = max(1, max_tokens - count("\n".join(header)))
        return ["\n".join([*header, piece]) for piece in _split_long("\n".join(lines[2:]), budget, count)]
    pieces, current = [], []
    for line in lines:
        if count(line) > max_tokens:
            pieces += ["\n".join(current)] if current else []
            current, words = [], []
            for word in line.split():
                if words and count(" ".join([*words, word])) > max_tokens:
                    pieces.append(" ".join(words))
                    words = []
                words.append(word)
            pieces += [" ".join(words)] if words else []
        elif current and count("\n".join([*current, line])) > max_tokens:
            pieces.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    return pieces + (["\n".join(current)] if current else [])


def chunk_document(doc_id: str, markdown: str, max_tokens: int = 400, overlap: int = 1,
                   count=approx_tokens) -> list[Chunk]:
    """Pack paragraphs into chunks within each section; the indexed text fits ``max_tokens``.

    ``count`` measures tokens (an estimate by default; pass the embedding model's tokenizer
    for exact budgets). The heading path that prefixes each chunk is part of the budget.
    ``overlap`` paragraphs from the end of one chunk start the next chunk of the same section.
    """
    chunks: list[Chunk] = []
    for headings, body in sections(markdown):
        budget = max(1, max_tokens - (count(" > ".join(headings)) if headings else 0))
        paragraphs = [piece for paragraph in _paragraphs(body)
                      for piece in (_split_long(paragraph, budget, count) if count(paragraph) > budget
                                    else [paragraph])]
        current: list[str] = []
        for paragraph in paragraphs:
            if current and count("\n\n".join([*current, paragraph])) > budget:
                chunks.append(Chunk(f"{doc_id}#{len(chunks)}", doc_id, headings, "\n\n".join(current)))
                kept = current[-overlap:] if overlap else []
                current = kept if count("\n\n".join([*kept, paragraph])) <= budget else []
            current.append(paragraph)
        if current:
            chunks.append(Chunk(f"{doc_id}#{len(chunks)}", doc_id, headings, "\n\n".join(current)))
    return chunks
