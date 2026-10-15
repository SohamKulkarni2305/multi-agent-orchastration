"""
project_summary_tool.py — High-level codebase architecture and metrics summary tool.
"""

import ast
from pathlib import Path


EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "docs", "skills"}


def get_project_summary(directory: str = ".") -> str:
    """
    Analyze codebase to report total lines of code, file counts, detected entrypoints,
    and high-level module descriptions.
    """
    root = Path(directory)
    if not root.is_dir():
        return f"Error: Directory not found: {directory}"

    py_files: list[Path] = []
    total_loc = 0
    modules_info: list[dict[str, str]] = []

    for path in sorted(root.rglob("*.py")):
        if set(path.parts).intersection(EXCLUDED_DIRS):
            continue

        py_files.append(path)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="latin-1", errors="replace")

        lines = [ln for ln in content.splitlines() if ln.strip()]
        total_loc += len(lines)

        # Extract top-level module docstring if present
        docstring = "No docstring."
        try:
            tree = ast.parse(content)
            doc = ast.get_docstring(tree)
            if doc:
                docstring = doc.strip().split("\n")[0]
        except Exception:
            pass

        rel = str(path.relative_to(root) if path.is_relative_to(root) else path).replace("\\", "/")
        modules_info.append({
            "path": rel,
            "loc": str(len(lines)),
            "doc": docstring,
        })

    # Detect potential entrypoints
    entrypoints: list[str] = []
    for mod in modules_info:
        p = mod["path"].lower()
        if "main.py" in p or "app.py" in p or "cli.py" in p:
            entrypoints.append(mod["path"])

    output = [
        f"=== Project Architecture & Codebase Summary: {root.resolve().name} ===",
        f"• Total Python Files : {len(py_files)}",
        f"• Total Lines of Code: ~{total_loc} lines",
        f"• Key Entrypoint(s)  : {', '.join(entrypoints) if entrypoints else 'None detected automatically'}",
        "\n--- Core Module Roster ---",
    ]

    for mod in modules_info:
        output.append(f"• {mod['path']} ({mod['loc']} lines)\n  Summary: {mod['doc']}")

    return "\n".join(output)
