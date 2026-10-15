"""
embedder.py — NVIDIA NIM Nemotron-3-Embed-1B (2048-dim) Vector Embeddings.
"""

import hashlib
import math
import os
from openai import OpenAI


EMBED_DIMENSION = 2048
DEFAULT_MODEL = "nvidia/nemotron-3-embed-1b"
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"


def _generate_mock_vector(text: str, input_type: str = "passage") -> list[float]:
    """
    Generate a deterministic, unit-normalized 2048-dimensional vector
    derived from the SHA-256 hash of the input text and input_type.
    """
    seed_str = f"{input_type}:{text}"
    hash_bytes = hashlib.sha256(seed_str.encode("utf-8")).digest()
    
    vec = []
    # Expand 32 bytes into 2048 floats deterministically
    for i in range(EMBED_DIMENSION):
        byte_val = hash_bytes[i % len(hash_bytes)]
        multiplier = ((i * 31 + byte_val) % 100) / 100.0 - 0.5
        vec.append(multiplier)

    # Unit-normalize the vector so dot product equals cosine similarity
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def get_embeddings(
    texts: list[str],
    input_type: str = "passage",
    model: str = DEFAULT_MODEL,
    mock: bool = False,
) -> list[list[float]]:
    """
    Generate 2048-dimensional vector embeddings for a list of texts.
    
    Args:
        texts: List of strings to embed.
        input_type: "passage" for documents/chunks, "query" for search queries.
        model: NVIDIA NIM embedding model name.
        mock: If True or if NVIDIA_API_KEY is unset, generates deterministic offline vectors.
        
    Returns:
        List of 2048-dimensional float lists.
    """
    if not texts:
        return []

    api_key = os.getenv("NVIDIA_API_KEY", "").strip() or os.getenv("NVIDIA_NIM_API_KEY", "").strip()
    base_url = os.getenv("NVIDIA_BASE_URL", DEFAULT_BASE_URL).strip()

    if mock or not api_key:
        return [_generate_mock_vector(t, input_type=input_type) for t in texts]

    client = OpenAI(base_url=base_url, api_key=api_key)
    response = client.embeddings.create(
        input=texts,
        model=model,
        extra_body={"input_type": input_type, "truncate": "END"},
    )

    embeddings: list[list[float]] = []
    for item in response.data:
        vec = item.embedding
        if len(vec) != EMBED_DIMENSION:
            raise ValueError(
                f"Expected embedding dimension {EMBED_DIMENSION}, got {len(vec)} from model {model}"
            )
        embeddings.append(vec)

    return embeddings
