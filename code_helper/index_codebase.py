import argparse
import ast
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path when executed directly as a script
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv

try:
    from .rag.chunker import chunk_file, evaluate_chunk_sizes
    from .rag.pinecone_client import ensure_pinecone_index, sync_chunks_to_pinecone
except ImportError:
    from code_helper.rag.chunker import chunk_file, evaluate_chunk_sizes
    from code_helper.rag.pinecone_client import ensure_pinecone_index, sync_chunks_to_pinecone


EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "code_helper",
    "tests",
    "docs",
    "skills",
    "build",
    "dist",
}


def filter_indexable_files(target_dir: str = ".") -> list[str]:
    """
    Scan target directory for indexable source files, explicitly excluding
    virtual environments, tests, code_helper implementation, git, and caches.
    """
    root = Path(target_dir)
    if not root.exists():
        return []

    indexable: list[str] = []
    candidates = list(root.rglob("*.py")) + list(root.rglob("*.txt"))

    for p in candidates:
        parts = set(p.parts)
        if parts.intersection(EXCLUDED_DIRS):
            continue
        if p.name.endswith(".json") or p.name.startswith("."):
            continue
        rel = str(p.relative_to(root) if p.is_relative_to(root) else p).replace("\\", "/")
        indexable.append(rel)

    return sorted(indexable)


def build_index(
    target_dir: str = ".",
    chunk_size: int = 500,
    overlap: int = 50,
    dry_run: bool = False,
    evaluate: bool = False,
    clean: bool = False,
    index_name: str = "code-helper",
) -> dict[str, Any]:
    """
    Scan codebase, chunk source files, and index into Pinecone using NVIDIA NIM.
    """
    # Load .env if present
    env_path = Path(target_dir) / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    files = filter_indexable_files(target_dir)
    all_chunks: list[dict[str, Any]] = []

    for rel_file in files:
        full_path = Path(target_dir) / rel_file
        try:
            chunks = chunk_file(str(full_path), chunk_size=chunk_size, overlap=overlap)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[!] Warning: Could not chunk {rel_file}: {e}")

    result: dict[str, Any] = {
        "files_scanned": len(files),
        "files_list": files,
        "chunks_processed": len(all_chunks),
        "chunk_size": chunk_size,
        "overlap": overlap,
        "dry_run": dry_run,
    }

    if evaluate:
        eval_queries: list[dict[str, str]] = []
        # Dynamically sample real identifiers from target codebase files
        for rel_file in files[:5]:
            full = Path(target_dir) / rel_file
            try:
                tree = ast.parse(full.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                        eval_queries.append({"target_keyword": node.name, "target_file": rel_file})
                        break
            except Exception:
                pass

        if not eval_queries and files:
            eval_queries = [{"target_keyword": "import", "target_file": files[0]}]

        result["evaluation"] = evaluate_chunk_sizes(
            target_dir=target_dir,
            sizes=[200, 500],
            overlap=overlap,
            eval_queries=eval_queries,
        )

    if dry_run:
        result["status"] = "Dry run completed successfully (no vectors upserted)."
        return result

    # Perform live Pinecone indexing
    api_key = os.getenv("PINECONE_API_KEY", "").strip()
    is_mock = not api_key

    ensure_pinecone_index(index_name=index_name, dimension=2048, mock=is_mock)
    upserted_count = sync_chunks_to_pinecone(
        all_chunks,
        index_name=index_name,
        batch_size=50,
        clean=clean,
        mock=is_mock,
    )

    result["vectors_upserted"] = upserted_count
    result["status"] = f"Successfully synced {upserted_count} chunks to Pinecone index '{index_name}'."
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Index codebase into Pinecone vector store via NVIDIA NIM.")
    parser.add_argument("--target-dir", default=".", help="Root directory of target codebase to index.")
    parser.add_argument("--chunk-size", type=int, default=500, help="Window size for character chunks (default: 500).")
    parser.add_argument("--overlap", type=int, default=50, help="Overlap characters between chunks (default: 50).")
    parser.add_argument("--dry-run", action="store_true", help="Scan and chunk without making live API calls.")
    parser.add_argument("--evaluate", action="store_true", help="Run comparative chunk size evaluation (200 vs 500 chars).")
    parser.add_argument("--clean", action="store_true", help="Clear existing vectors before upserting.")
    parser.add_argument("--index-name", default="code-helper", help="Pinecone index name (default: 'code-helper').")

    args = parser.parse_args()

    print("==================================================")
    print("  CODE HELPER: CODEBASE VECTOR INDEXER")
    print("==================================================")
    print(f"[*] Target Directory: {Path(args.target_dir).resolve()}")
    print(f"[*] Chunk Size      : {args.chunk_size}")
    print(f"[*] Overlap         : {args.overlap}")
    print(f"[*] Dry Run Mode    : {args.dry_run}")
    print(f"[*] Clean Old Index : {args.clean}")
    print("--------------------------------------------------")

    res = build_index(
        target_dir=args.target_dir,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        dry_run=args.dry_run,
        evaluate=args.evaluate,
        clean=args.clean,
        index_name=args.index_name,
    )

    print(f"[OK] Files Scanned    : {res['files_scanned']}")
    print(f"[OK] Chunks Processed : {res['chunks_processed']}")
    if "evaluation" in res:
        print("\n=== Chunk Size Evaluation Benchmark ===")
        for size, stats in res["evaluation"].items():
            print(f"• Size {size} chars: {stats['chunk_count']} chunks | Avg: {stats['avg_chars']} chars | Recall: {int(stats['recall_rate']*100)}%")

    print(f"\n[STATUS] {res['status']}\n")


if __name__ == "__main__":
    main()
