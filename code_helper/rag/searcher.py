"""
searcher.py — Vector Similarity Retrieval & Formatted Result Synthesis.
"""

import math
import os
from typing import Any
from .embedder import get_embeddings
from .pinecone_client import get_pinecone_client, _MOCK_STORE


FALLBACK_MESSAGE = "I could not find that"


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def rag_search(
    query: str,
    index_name: str = "code-helper",
    top_k: int = 3,
    threshold: float = 0.45,
    mock: bool = False,
) -> str:
    """
    Search indexed codebase vectors for passages relevant to query.
    
    Returns:
        Formatted citations with file and line ranges, or "I could not find that"
        if no results pass the relevance threshold.
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        return FALLBACK_MESSAGE

    api_key = os.getenv("PINECONE_API_KEY", "").strip()
    is_mock = mock or not api_key

    query_embeddings = get_embeddings([cleaned_query], input_type="query", mock=is_mock)
    if not query_embeddings:
        return FALLBACK_MESSAGE

    query_vec = query_embeddings[0]

    matches: list[dict[str, Any]] = []

    if is_mock:
        # Search in-memory mock store
        store_items = _MOCK_STORE.get(index_name, [])
        if not store_items and _MOCK_STORE:
            # Fall back to any active mock index
            for v in _MOCK_STORE.values():
                store_items.extend(v)

        scored: list[tuple[float, dict[str, Any]]] = []
        for item in store_items:
            sim = _cosine_similarity(query_vec, item["values"])
            if sim >= threshold:
                scored.append((sim, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        for sim, item in scored[:top_k]:
            meta = item.get("metadata", {})
            matches.append({
                "score": sim,
                "file_path": meta.get("file_path", "unknown"),
                "start_line": meta.get("start_line", 1),
                "end_line": meta.get("end_line", 1),
                "text": meta.get("text", ""),
            })
    else:
        client = get_pinecone_client(mock=False)
        if client is None:
            return FALLBACK_MESSAGE

        index = client.Index(index_name)
        res = index.query(
            vector=query_vec,
            top_k=top_k,
            include_metadata=True,
        )

        for match in res.matches:
            if match.score >= threshold:
                meta = match.metadata or {}
                matches.append({
                    "score": match.score,
                    "file_path": meta.get("file_path", "unknown"),
                    "start_line": meta.get("start_line", 1),
                    "end_line": meta.get("end_line", 1),
                    "text": meta.get("text", ""),
                })

    if not matches:
        return FALLBACK_MESSAGE

    formatted_parts: list[str] = []
    for i, m in enumerate(matches, start=1):
        formatted_parts.append(
            f"--- Match {i} | {m['file_path']}:{m['start_line']}-{m['end_line']} (Score: {m['score']:.3f}) ---\n"
            f"{m['text'].strip()}"
        )

    return "\n\n".join(formatted_parts)
