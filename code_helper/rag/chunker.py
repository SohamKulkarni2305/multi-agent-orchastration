"""
chunker.py — Line-preserving chunking and chunk-size evaluation for Codebase RAG.
"""

from pathlib import Path
from typing import Any


def chunk_file(
    file_path: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """
    Split a source file into overlapping, line-preserving text chunks.
    Preserves exact 1-based start and end line numbers and relative path.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="latin-1", errors="replace")

    lines = content.splitlines(keepends=True)
    if not lines:
        return []

    # Store (line_index_1_based, line_text, char_length)
    indexed_lines = [(i + 1, line) for i, line in enumerate(lines)]

    chunks: list[dict[str, Any]] = []
    start_idx = 0
    total_lines = len(indexed_lines)
    rel_path_str = str(path).replace("\\", "/")

    chunk_seq = 0
    while start_idx < total_lines:
        cur_chars = 0
        end_idx = start_idx
        chunk_line_texts: list[str] = []

        while end_idx < total_lines:
            line_str = indexed_lines[end_idx][1]
            if cur_chars + len(line_str) > chunk_size and cur_chars > 0:
                break
            chunk_line_texts.append(line_str)
            cur_chars += len(line_str)
            end_idx += 1

        if not chunk_line_texts:
            # Single line exceeds chunk_size, include it anyway
            chunk_line_texts.append(indexed_lines[start_idx][1])
            cur_chars += len(chunk_line_texts[0])
            end_idx = start_idx + 1

        start_line = indexed_lines[start_idx][0]
        end_line = indexed_lines[end_idx - 1][0]
        chunk_text = "".join(chunk_line_texts)

        chunks.append({
            "chunk_id": f"{rel_path_str}:chunk_{chunk_seq}:L{start_line}-L{end_line}",
            "file_path": rel_path_str,
            "start_line": start_line,
            "end_line": end_line,
            "text": chunk_text,
            "char_count": len(chunk_text),
        })
        chunk_seq += 1

        if end_idx >= total_lines:
            break

        # Calculate step back for overlap
        overlap_chars = 0
        step_back_idx = end_idx - 1
        while step_back_idx > start_idx and overlap_chars < overlap:
            overlap_chars += len(indexed_lines[step_back_idx][1])
            step_back_idx -= 1

        next_start = step_back_idx + 1
        if next_start <= start_idx:
            next_start = start_idx + 1
        start_idx = next_start

    return chunks


def evaluate_chunk_sizes(
    target_dir: str,
    sizes: list[int] = [200, 500],
    overlap: int = 50,
    eval_queries: list[dict[str, str]] | None = None,
) -> dict[int, dict[str, Any]]:
    """
    Empirically evaluate chunk distributions and retrieval hits across multiple chunk sizes.
    """
    root = Path(target_dir)
    excluded = {".git", ".venv", "__pycache__", "code_helper", "tests", "docs", "skills", ".pytest_cache"}

    py_files: list[Path] = []
    if root.is_file():
        py_files = [root]
    else:
        for p in root.rglob("*.py"):
            parts = set(p.parts)
            if not parts.intersection(excluded):
                py_files.append(p)

    results: dict[int, dict[str, Any]] = {}

    for size in sizes:
        eff_overlap = min(overlap, size // 4)
        all_chunks: list[dict[str, Any]] = []
        for f in py_files:
            try:
                all_chunks.extend(chunk_file(str(f), chunk_size=size, overlap=eff_overlap))
            except Exception:
                continue

        total_chunks = len(all_chunks)
        char_counts = [c["char_count"] for c in all_chunks]
        avg_chars = sum(char_counts) / total_chunks if total_chunks > 0 else 0
        min_chars = min(char_counts) if total_chunks > 0 else 0
        max_chars = max(char_counts) if total_chunks > 0 else 0

        # Evaluate keyword retrieval recall if eval queries provided
        recall_hits = 0
        if eval_queries and all_chunks:
            for q in eval_queries:
                target_word = q.get("target_keyword", "").lower()
                target_file = q.get("target_file", "").lower()
                hit = any(
                    target_word in c["text"].lower() and (not target_file or target_file in c["file_path"].lower())
                    for c in all_chunks
                )
                if hit:
                    recall_hits += 1
            recall_rate = recall_hits / len(eval_queries)
        else:
            recall_rate = 1.0 if total_chunks > 0 else 0.0

        results[size] = {
            "chunk_count": total_chunks,
            "total_chunks": total_chunks,  # backwards-compatible key
            "avg_chars": round(avg_chars, 1),
            "min_chars": min_chars,
            "max_chars": max_chars,
            "recall_rate": recall_rate,
            "files_evaluated": len(py_files),
        }

    return results
