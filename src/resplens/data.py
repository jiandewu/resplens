"""Access to a pinned ObsAwareData release: download, checksum, cache, and DuckDB views.

ObsAwareData (https://github.com/DMA-PRIME/ObsAwareData, CC BY 4.0) publishes weekly
NHSN, NSSP, and NWSS respiratory surveillance data for the 50 states and DC. Files are
read from one tagged release so that results are reproducible; every file under data/
and every revision-history asset is checked against its published SHA-256.
"""

from __future__ import annotations

import csv
import hashlib
import os
import shutil
import threading
import urllib.parse
import urllib.request
from functools import cached_property
from pathlib import Path

import duckdb


DATA_TAG = "v2.0.0+2026-10-16"
REPO = "DMA-PRIME/ObsAwareData"


class DataError(ValueError):
    """Bad request against the dataset (unknown state, missing file, checksum mismatch)."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _sql_paths(paths: list[str]) -> str:
    """SQL list literal of file paths (DDL statements cannot take bound parameters)."""
    return "[" + ", ".join("'" + path.replace("'", "''") + "'" for path in paths) + "]"


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class Dataset:
    """One ObsAwareData release.

    With ``mirror`` set, files are read from a local directory laid out like the
    repository (plus ``releases/`` for revision-history assets); nothing is downloaded.
    Otherwise files are downloaded on first use into ``cache_dir``.
    """

    def __init__(self, tag: str = DATA_TAG, cache_dir: Path | None = None, mirror: Path | None = None):
        self.tag = tag
        self.mirror = Path(mirror) if mirror else None
        default_cache = Path(os.environ.get("RESPLENS_CACHE", Path.home() / ".cache" / "resplens"))
        self.cache_dir = Path(cache_dir or default_cache) / tag
        self.con = duckdb.connect()
        self._views: set[str] = set()
        self._lock = threading.Lock()  # MCP tools may run in worker threads

    # -- files -------------------------------------------------------------

    def _raw_url(self, path: str) -> str:
        return f"https://raw.githubusercontent.com/{REPO}/{urllib.parse.quote(self.tag, safe='')}/{path}"

    def _download(self, url: str, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + ".part")
        with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        partial.replace(target)

    def _verified(self, path: Path, expected: str | None) -> Path:
        if expected and _sha256(path) != expected.lower():
            raise DataError(f"checksum mismatch for {path.name}; delete it and retry")
        return path

    def file(self, path: str) -> Path:
        """Local copy of a repository file, verified against the manifest when it is under data/."""
        expected = self.manifest.get(path) if path.startswith("data/") else None
        if path.startswith("data/") and expected is None:
            raise DataError(f"{path} is not in the {self.tag} manifest")
        if self.mirror:
            local = self.mirror / path
            if not local.exists():
                raise DataError(f"{path} is missing from the mirror {self.mirror}")
            return self._verified(local, expected)
        local = self.cache_dir / path
        if not local.exists():
            self._download(self._raw_url(path), local)
        return self._verified(local, expected)

    def release_asset(self, row: dict) -> Path:
        """Local copy of one revision-history file listed in metadata/release_assets.csv."""
        if self.mirror:
            local = self.mirror / "releases" / row["file"]
            if not local.exists():
                raise DataError(f"{row['file']} is missing from the mirror {self.mirror}")
        else:
            local = self.cache_dir / "releases" / row["file"]
            if not local.exists():
                self._download(row["url"], local)
        return self._verified(local, row["sha256"])

    # -- metadata ----------------------------------------------------------

    @cached_property
    def manifest(self) -> dict[str, str]:
        if self.mirror:
            path = self.mirror / "metadata" / "manifest.csv"
        else:
            path = self.cache_dir / "metadata" / "manifest.csv"
            if not path.exists():
                self._download(self._raw_url("metadata/manifest.csv"), path)
        return {row["path"]: row["sha256"] for row in _read_csv(path)}

    def _metadata(self, name: str) -> list[dict]:
        return _read_csv(self.file(f"metadata/{name}"))

    @cached_property
    def coverage(self) -> dict[str, dict]:
        return {row["state"]: row for row in self._metadata("coverage_summary.csv")}

    @cached_property
    def thresholds(self) -> dict[str, dict]:
        return {row["state"]: row for row in self._metadata("observation_state_thresholds.csv")}

    @cached_property
    def release_assets(self) -> list[dict]:
        return self._metadata("release_assets.csv")

    def state(self, code: str) -> str:
        """Normalized two-letter state code; raises DataError for unknown codes."""
        state = (code or "").strip().upper()
        if state not in self.coverage:
            raise DataError(f"unknown state {code!r}; use a two-letter postal code such as SC or DC")
        return state

    # -- tables ------------------------------------------------------------

    def latest(self, state: str) -> str:
        """Name of a DuckDB view over the state's latest-value long table (all columns text)."""
        state = self.state(state)
        view = f"latest_{state.lower()}"
        with self._lock:
            if view in self._views:
                return view
            prefix = f"data/{state}/{state.lower()}_long_latest_"
            paths = [str(self.file(path)) for path in sorted(self.manifest) if path.startswith(prefix)]
            if not paths:
                raise DataError(f"no latest-value files for {state} in {self.tag}")
            self.con.execute(f"CREATE VIEW {view} AS SELECT * FROM read_csv({_sql_paths(paths)}, all_varchar = true, "
                             "header = true, delim = ',', quote = '\"', escape = '\"')")
            self._views.add(view)
            return view

    def versions(self, state: str) -> str:
        """Name of a DuckDB table with every published version of every value for the state.

        The full file and its increments are concatenated in the order listed in
        release_assets.csv. The first call downloads the files (tens of MB for large states).
        """
        state = self.state(state)
        view = f"versions_{state.lower()}"
        with self._lock:
            if view in self._views:
                return view
            rows = [row for row in self.release_assets if row["state"] == state]
            if not rows or rows[0]["kind"] != "full":
                raise DataError(f"no revision history for {state} in {self.tag}")
            paths = [str(self.release_asset(row)) for row in rows]
            self.con.execute(f"CREATE TABLE {view} AS SELECT * FROM read_csv({_sql_paths(paths)}, all_varchar = true, "
                             "header = true, delim = ',', quote = '\"', escape = '\"', union_by_name = true)")
            self._views.add(view)
            return view

    def query(self, sql: str, params: list | None = None) -> list[dict]:
        cursor = self.con.cursor().execute(sql, params or [])
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
