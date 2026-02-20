from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from broke.config import get_settings

log = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None
_embed_fn: SentenceTransformerEmbeddingFunction | None = None


def _get_embed_fn() -> SentenceTransformerEmbeddingFunction:
    global _embed_fn
    if _embed_fn is None:
        settings = get_settings()
        _embed_fn = SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model,
        )
    return _embed_fn


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(path=settings.chroma_path)
        log.info("ChromaDB initialised at %s", settings.chroma_path)
    return _client


def get_or_create_collection(name: str) -> chromadb.Collection:
    return get_client().get_or_create_collection(
        name=name,
        embedding_function=_get_embed_fn(),
    )


def add_documents(
    collection_name: str,
    documents: list[str],
    metadatas: list[dict[str, Any]] | None = None,
    ids: list[str] | None = None,
) -> None:
    coll = get_or_create_collection(collection_name)
    if ids is None:
        ids = [f"{collection_name}_{i}" for i in range(len(documents))]
    coll.upsert(documents=documents, metadatas=metadatas, ids=ids)
    log.info("Upserted %d docs into '%s'", len(documents), collection_name)


def query(
    collection_name: str,
    query_text: str,
    n_results: int = 5,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Query a collection and return a flat list of result dicts."""
    coll = get_or_create_collection(collection_name)
    kwargs: dict[str, Any] = {
        "query_texts": [query_text],
        "n_results": min(n_results, coll.count() or 1),
    }
    if where:
        kwargs["where"] = where

    if coll.count() == 0:
        return []

    results = coll.query(**kwargs)
    out: list[dict[str, Any]] = []
    for i, doc in enumerate(results["documents"][0]):
        entry: dict[str, Any] = {"text": doc}
        if results["metadatas"] and results["metadatas"][0]:
            entry["metadata"] = results["metadatas"][0][i]
        if results["distances"] and results["distances"][0]:
            entry["distance"] = results["distances"][0][i]
        out.append(entry)
    return out
