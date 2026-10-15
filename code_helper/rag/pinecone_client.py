"""
pinecone_client.py — Pinecone Serverless Index Management & Vector Sync.
"""

import os
import time
from typing import Any
from pinecone import Pinecone, ServerlessSpec
from .embedder import get_embeddings, EMBED_DIMENSION


# Global in-memory storage for offline testing and mock mode
_MOCK_STORE: dict[str, list[dict[str, Any]]] = {}


def get_pinecone_client(mock: bool = False) -> Pinecone | None:
    """
    Return an authenticated Pinecone client, or None if in mock mode or unconfigured.
    """
    if mock:
        return None
    api_key = os.getenv("PINECONE_API_KEY", "").strip()
    if not api_key:
        return None
    return Pinecone(api_key=api_key)


def ensure_pinecone_index(
    index_name: str = "code-helper",
    dimension: int = EMBED_DIMENSION,
    metric: str = "cosine",
    cloud: str = "aws",
    region: str = "us-east-1",
    mock: bool = False,
) -> Any:
    """
    Idempotently ensure that the Pinecone index exists and is ready for operations.
    """
    if mock:
        if index_name not in _MOCK_STORE:
            _MOCK_STORE[index_name] = []
        return {"name": index_name, "status": {"ready": True}, "mock": True}

    client = get_pinecone_client(mock=False)
    if client is None:
        if index_name not in _MOCK_STORE:
            _MOCK_STORE[index_name] = []
        return {"name": index_name, "status": {"ready": True}, "mock": True}

    existing_indexes = [idx.name for idx in client.list_indexes()]
    if index_name not in existing_indexes:
        client.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud=cloud, region=region),
        )
        # Await index readiness
        for _ in range(60):
            desc = client.describe_index(index_name)
            if desc.status.get("ready", False):
                break
            time.sleep(1)

    return client.Index(index_name)


def sync_chunks_to_pinecone(
    chunks: list[dict[str, Any]],
    index_name: str = "code-helper",
    batch_size: int = 50,
    clean: bool = False,
    mock: bool = False,
) -> int:
    """
    Embed and upsert chunks to Pinecone in batches.
    
    Returns:
        Total number of vectors upserted.
    """
    if not chunks:
        return 0

    api_key = os.getenv("PINECONE_API_KEY", "").strip()
    is_mock = mock or not api_key

    # Extract text strings and generate embeddings
    texts = [c["text"] for c in chunks]
    embeddings = get_embeddings(texts, input_type="passage", mock=is_mock)

    if is_mock:
        if clean or index_name not in _MOCK_STORE:
            _MOCK_STORE[index_name] = []
        
        for c, emb in zip(chunks, embeddings):
            _MOCK_STORE[index_name].append({
                "id": c["chunk_id"],
                "values": emb,
                "metadata": {
                    "file_path": c["file_path"],
                    "start_line": c["start_line"],
                    "end_line": c["end_line"],
                    "text": c["text"],
                }
            })
        return len(chunks)

    client = get_pinecone_client(mock=False)
    if client is None:
        return 0

    index = client.Index(index_name)
    if clean:
        try:
            index.delete(delete_all=True)
        except Exception:
            pass

    records: list[dict[str, Any]] = []
    for c, emb in zip(chunks, embeddings):
        records.append({
            "id": c["chunk_id"],
            "values": emb,
            "metadata": {
                "file_path": c["file_path"],
                "start_line": c["start_line"],
                "end_line": c["end_line"],
                "text": c["text"][:1000],  # Pinecone metadata size guard
            }
        })

    # Batch upsert
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        index.upsert(vectors=batch)

    return len(records)
