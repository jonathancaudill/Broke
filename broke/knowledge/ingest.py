"""Load markdown knowledge files, chunk by section, and store in ChromaDB."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from broke.knowledge.store import add_documents

log = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge_data"

# Splits on markdown headings (## or ###)
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


def _chunk_markdown(text: str, source: str) -> list[tuple[str, dict[str, Any]]]:
    """Split markdown text into (chunk_text, metadata) tuples by heading."""
    chunks: list[tuple[str, dict[str, Any]]] = []
    positions = [(m.start(), m.group(1), m.group(2)) for m in _HEADING_RE.finditer(text)]

    if not positions:
        return [(text.strip(), {"source": source, "section": "root"})]

    # Text before first heading
    preamble = text[: positions[0][0]].strip()
    if preamble:
        chunks.append((preamble, {"source": source, "section": "preamble"}))

    for idx, (start, _level, heading) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
        body = text[start:end].strip()
        if body:
            chunks.append((body, {"source": source, "section": heading}))

    return chunks


def ingest_file(filepath: Path, collection: str | None = None) -> int:
    """Ingest a single markdown file into ChromaDB. Returns chunk count."""
    collection_name = collection or filepath.stem
    text = filepath.read_text(encoding="utf-8")
    chunks = _chunk_markdown(text, source=filepath.name)
    if not chunks:
        return 0

    documents = [c[0] for c in chunks]
    metadatas = [c[1] for c in chunks]
    ids = [f"{collection_name}_{i}" for i in range(len(chunks))]
    add_documents(collection_name, documents, metadatas, ids)
    log.info("Ingested %d chunks from %s -> %s", len(chunks), filepath.name, collection_name)
    return len(chunks)


def ingest_all() -> dict[str, int]:
    """Ingest every .md file in knowledge_data/. Returns {filename: chunk_count}."""
    results: dict[str, int] = {}
    if not KNOWLEDGE_DIR.exists():
        log.warning("Knowledge directory not found: %s", KNOWLEDGE_DIR)
        return results

    for md_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
        count = ingest_file(md_file)
        results[md_file.name] = count

    log.info("Ingestion complete: %s", results)
    return results
