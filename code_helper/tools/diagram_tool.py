"""
diagram_tool.py — Deterministic Mermaid Architecture Diagram Generator.
"""

import ast
from pathlib import Path


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
    "code_helper",
    "tests",
    "docs",
    "skills",
}


def generate_architecture_diagram(project_dir: str = ".") -> str:
    """
    Generate a clean, valid Mermaid flowchart diagram (graph TD) showing
    the architectural module dependencies and call relationships across the codebase.
    Use this tool when a developer asks for a diagram, flowchart, or visual map of the project.
    """
    root = Path(project_dir)
    if not root.exists():
        return f"Error: Project directory '{project_dir}' not found."

    py_files = sorted(root.glob("*.py"))
    if not py_files:
        py_files = sorted(root.rglob("*.py"))

    # Filter out excluded directories
    valid_files: list[Path] = []
    for f in py_files:
        if not set(f.parts).intersection(EXCLUDE_DIRS):
            valid_files.append(f)

    if not valid_files:
        return "No valid Python files found to diagram."

    edges: list[tuple[str, str, str]] = []
    file_stems = {f.stem: f.name for f in valid_files}

    for f in valid_files:
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except Exception:
            continue

        caller = f.name
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base = alias.name.split(".")[0]
                    if base in file_stems and file_stems[base] != caller:
                        target = file_stems[base]
                        edges.append((caller, target, "imports"))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base = node.module.split(".")[0]
                    if base in file_stems and file_stems[base] != caller:
                        target = file_stems[base]
                        names = ", ".join(a.name for a in node.names[:2])
                        edges.append((caller, target, names))

    # Build Mermaid syntax
    unique_edges = sorted(set(edges))
    lines = [
        "```mermaid",
        "graph TD",
        "    %% Core Component Nodes",
    ]

    for f in valid_files:
        node_id = f.stem.replace("-", "_")
        lines.append(f'    {node_id}["{f.name}"]')

    lines.append("    %% Dependency Edges")
    for src, dst, label in unique_edges:
        src_id = Path(src).stem.replace("-", "_")
        dst_id = Path(dst).stem.replace("-", "_")
        lines.append(f'    {src_id} -->|"{label}"| {dst_id}')

    lines.append("```")

    explanation = (
        "=== Architecture Dependency Diagram (Mermaid) ===\n\n"
        + "\n".join(lines)
        + "\n\n*Note: Render this diagram in any Markdown viewer or IDE preview to visualize module dependencies.*"
    )
    return explanation
