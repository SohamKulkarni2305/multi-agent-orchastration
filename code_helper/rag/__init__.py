"""
RAG pipeline subpackage for Code Helper.
"""
from .chunker import chunk_file, evaluate_chunk_sizes
from .embedder import get_embeddings
from .pinecone_client import ensure_pinecone_index, sync_chunks_to_pinecone
from .searcher import rag_search

__all__ = [
    "chunk_file",
    "evaluate_chunk_sizes",
    "get_embeddings",
    "ensure_pinecone_index",
    "sync_chunks_to_pinecone",
    "rag_search",
]
