"""
code_inspection_tools.py — Source code extraction and AST symbol isolation.
"""

import ast
from pathlib import Path


def get_function_source(file_path: str, symbol_name: str) -> str:
    """
    Extract the exact source code, docstring, and line boundaries for a specified
    function, class, or method from a Python file.
    Use this tool when you need to inspect or explain a specific function definition directly.
    """
    target = Path(file_path)
    if not target.exists():
        # Try resolving relative to current working directory
        cwd_target = Path.cwd() / file_path
        if cwd_target.exists():
            target = cwd_target
        else:
            return f"Error: File '{file_path}' does not exist."

    try:
        source = target.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(target))
    except Exception as e:
        return f"Error reading or parsing '{file_path}': {e}"

    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol_name:
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", start_line)
                
                # Extract code slice
                symbol_lines = lines[start_line - 1 : end_line]
                kind = "Class" if isinstance(node, ast.ClassDef) else "Function"
                
                docstring = ast.get_docstring(node) or "No docstring provided."
                
                output = [
                    f"=== {kind} '{symbol_name}' in {target.name} (Lines {start_line}-{end_line}) ===",
                    f"Docstring: {docstring.strip()}",
                    "--- Source Code ---",
                ]
                for idx, line in enumerate(symbol_lines, start=start_line):
                    output.append(f"{idx:4d} | {line}")
                
                return "\n".join(output)

    return f"Symbol '{symbol_name}' was not found in '{file_path}'."
