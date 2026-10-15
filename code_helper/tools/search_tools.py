"""
search_tools.py — Exact text and regex pattern matching tool.
"""

from pathlib import Path
import re


EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "build",
    "dist",
    "docs",
    "skills",
}


def find_exact_matches(
    query: str,
    project_dir: str = ".",
    file_pattern: str = "*.py",
) -> str:
    """
    Search for exact text or regex pattern matches across source files.
    Use this tool when you need exact code occurrences, variable declarations,
    or keyword lookups with exact file and line numbers.
    """
    root = Path(project_dir)
    if not root.exists():
        return f"Error: Project directory '{project_dir}' not found."

    cleaned_query = query.strip()
    if not cleaned_query:
        return "Please provide a non-empty search query."

    try:
        pattern = re.compile(re.escape(cleaned_query), re.IGNORECASE)
    except Exception as e:
        return f"Invalid search pattern: {e}"

    results: list[str] = []
    total_matches = 0

    candidates = sorted(root.rglob(file_pattern))
    for file_path in candidates:
        # Check excluded directories
        if set(file_path.parts).intersection(EXCLUDE_DIRS):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        file_matches: list[str] = []
        for line_no, line in enumerate(content.splitlines(), start=1):
            if pattern.search(line):
                rel_path = file_path.relative_to(root) if file_path.is_relative_to(root) else file_path
                file_matches.append(f"  Line {line_no:3d}: {line.strip()}")
                total_matches += 1

        if file_matches:
            rel_name = str(file_path.relative_to(root) if file_path.is_relative_to(root) else file_path).replace("\\", "/")
            results.append(f"=== {rel_name} ({len(file_matches)} matches) ===")
            results.extend(file_matches[:10])  # Cap at 10 matches per file
            if len(file_matches) > 10:
                results.append(f"  ... and {len(file_matches) - 10} more matches in this file.")
            results.append("")

    if not results:
        return f"No exact matches found for '{query}' across {file_pattern} files."

    header = f"Found {total_matches} match(es) for '{query}':\n\n"
    return header + "\n".join(results)
