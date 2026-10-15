"""
metrics_tool.py — Calculates lines of code, comments, classes, functions, and docstring coverage.
"""

import ast
from pathlib import Path


def calculate_code_metrics(file_path: str) -> str:
    """
    Compute comprehensive code metrics for a specified Python file.
    """
    path = Path(file_path)
    if not path.is_file():
        return f"Error: File not found: {file_path}"

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="latin-1", errors="replace")

    raw_lines = content.splitlines()
    total_lines = len(raw_lines)
    blank_lines = 0
    comment_lines = 0
    code_lines = 0

    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
        elif stripped.startswith("#"):
            comment_lines += 1
        else:
            code_lines += 1

    functions_count = 0
    classes_count = 0
    docstrings_count = 0

    try:
        tree = ast.parse(content, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions_count += 1
                if ast.get_docstring(node):
                    docstrings_count += 1
            elif isinstance(node, ast.ClassDef):
                classes_count += 1
                if ast.get_docstring(node):
                    docstrings_count += 1
    except SyntaxError as e:
        return f"SyntaxError parsing {file_path}: {e}"

    total_symbols = functions_count + classes_count
    docstring_coverage = (
        round((docstrings_count / total_symbols) * 100, 1)
        if total_symbols > 0
        else 100.0
    )

    output = [
        f"=== Code Metrics for '{path.name}' ===",
        f"• Total Lines       : {total_lines}",
        f"• Lines of Code     : {code_lines}",
        f"• Comment Lines     : {comment_lines}",
        f"• Blank Lines       : {blank_lines}",
        f"• Classes           : {classes_count}",
        f"• Functions/Methods : {functions_count}",
        f"• Docstring Coverage: {docstring_coverage}% ({docstrings_count}/{total_symbols} documented)",
    ]

    return "\n".join(output)
