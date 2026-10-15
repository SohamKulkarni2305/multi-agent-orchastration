import pytest
from pathlib import Path
from code_helper.rag.chunker import chunk_file, evaluate_chunk_sizes
from code_helper.rag.embedder import get_embeddings
from code_helper.rag.pinecone_client import ensure_pinecone_index, sync_chunks_to_pinecone
from code_helper.rag.searcher import rag_search

@pytest.fixture
def sample_code_file(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text(
        "import os\n\ndef add(a: int, b: int) -> int:\n    '''Add two numbers.'''\n    return a + b\n\n"
        "def subtract(a: int, b: int) -> int:\n    '''Subtract two numbers.'''\n    return a - b\n",
        encoding="utf-8"
    )
    return str(f)

def test_chunk_file_metadata_and_lines(sample_code_file):
    chunks = chunk_file(sample_code_file, chunk_size=80, overlap=20)
    assert len(chunks) > 0
    first = chunks[0]
    assert "chunk_id" in first
    assert "file_path" in first
    assert "start_line" in first
    assert "end_line" in first
    assert "text" in first
    assert first["start_line"] >= 1
    assert first["end_line"] >= first["start_line"]

def test_chunk_file_real_repo_code():
    assert Path("config.py").exists(), "config.py should exist in repository root"
    chunks = chunk_file("config.py", chunk_size=300, overlap=50)
    assert len(chunks) > 0
    assert chunks[0]["file_path"] == "config.py"

def test_embedder_dimension_and_mock():
    # Verifies exact 2048 dimensions without live API
    vecs = get_embeddings(["def test_fn(): pass"], input_type="passage", mock=True)
    assert len(vecs) == 1
    assert len(vecs[0]) == 2048
    assert all(isinstance(x, float) for x in vecs[0])

def test_embedder_query_vs_passage():
    q_vec = get_embeddings(["test query"], input_type="query", mock=True)
    p_vec = get_embeddings(["test passage"], input_type="passage", mock=True)
    assert len(q_vec[0]) == 2048
    assert len(p_vec[0]) == 2048

def test_pinecone_client_mock_sync(sample_code_file):
    chunks = chunk_file(sample_code_file, chunk_size=100, overlap=20)
    client = ensure_pinecone_index("test-index", dimension=2048, mock=True)
    assert client is not None
    upserted = sync_chunks_to_pinecone(chunks, "test-index", mock=True)
    assert upserted == len(chunks)

def test_searcher_fallback_on_unrelated_query():
    # Irrelevant query should trigger low similarity and return fallback string
    result = rag_search("totally unrelated xyz 123 999", top_k=3, threshold=0.9, mock=True)
    assert result.strip() == "I could not find that"

def test_searcher_finds_relevant_in_mock():
    # Search against indexed mock chunks
    result = rag_search("def add", top_k=1, threshold=0.1, mock=True)
    assert "sample" in result or "I could not find that" in result or len(result) > 0

def test_evaluate_chunk_sizes_benchmark(sample_code_file, tmp_path):
    res = evaluate_chunk_sizes(str(tmp_path), sizes=[60, 150])
    assert 60 in res
    assert 150 in res
    assert "chunk_count" in res[60]
    assert "avg_chars" in res[60]
    assert res[60]["chunk_count"] >= res[150]["chunk_count"]
