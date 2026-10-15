"""
plain_ast_tools.py — AST and Filesystem Inspection Tools (Plain Python, Strictly No AI).
"""

import ast
from pathlib import Path
from typing import Any


EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "docs", "skills"}


def _read_file_safe(file_path: Path) -> str:
    """Read file content safely with fallback encoding."""
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1", errors="replace")


def find_imports(target_file_or_module: str, project_dir: str = ".") -> str:
    """
    Find what a file imports, or find all project files that import a given module.
    
    If target_file_or_module is a file path, returns all modules imported by that file.
    If it is a module name, scans the project for files importing that module.
    """
    target_path = Path(target_file_or_module)
    proj_path = Path(project_dir)

    # Mode 1: Inspect a specific file's imports
    if target_path.is_file() or target_file_or_module.endswith(".py"):
        if not target_path.is_file():
            # Try resolving relative to project_dir
            target_path = proj_path / target_file_or_module
        if not target_path.is_file():
            return f"Error: File not found: {target_file_or_module}"

        try:
            tree = ast.parse(_read_file_safe(target_path), filename=str(target_path))
        except SyntaxError as e:
            return f"SyntaxError in {target_path}: {e}"

        direct_imports: list[str] = []
        from_imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    direct_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                names = [a.name for a in node.names]
                from_imports.append(f"from {mod} import {', '.join(names)}")

        output = [f"=== Imports in '{target_file_or_module}' ==="]
        if direct_imports:
            output.append("Standard / Direct Imports:")
            for imp in sorted(set(direct_imports)):
                output.append(f"  - import {imp}")
        if from_imports:
            output.append("From Imports:")
            for f_imp in sorted(set(from_imports)):
                output.append(f"  - {f_imp}")

        if not direct_imports and not from_imports:
            output.append("No imports found.")
        return "\n".join(output)

    # Mode 2: Reverse lookup — find which files import a given module name
    module_query = target_file_or_module.replace(".py", "").strip()
    matches: list[str] = []

    for py_file in proj_path.rglob("*.py"):
        if set(py_file.parts).intersection(EXCLUDED_DIRS):
            continue

        try:
            tree = ast.parse(_read_file_safe(py_file), filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        found = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if module_query in alias.name:
                        found = True
                        break
            elif isinstance(node, ast.ImportFrom):
                if node.module and module_query in node.module:
                    found = True
                    break
                for alias in node.names:
                    if module_query == alias.name:
                        found = True
                        break
            if found:
                break

        if found:
            rel = str(py_file.relative_to(proj_path) if py_file.is_relative_to(proj_path) else py_file).replace("\\", "/")
            matches.append(rel)

    if not matches:
        return f"No files found importing module '{module_query}' in {project_dir}"

    output = [f"=== Files importing '{module_query}' ==="]
    for m in sorted(matches):
        output.append(f"  - {m}")
    return "\n".join(output)


def find_symbol_references(symbol_name: str, project_dir: str = ".") -> str:
    """
    Scan project ASTs to locate all usages, call sites, and definitions of a symbol.
    """
    proj_path = Path(project_dir)
    if not proj_path.is_dir():
        return f"Error: Project directory not found: {project_dir}"

    references: list[dict[str, Any]] = []

    for py_file in proj_path.rglob("*.py"):
        if set(py_file.parts).intersection(EXCLUDED_DIRS):
            continue

        try:
            content = _read_file_safe(py_file)
            tree = ast.parse(content, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        lines = content.splitlines()

        for node in ast.walk(tree):
            is_match = False
            kind = "usage"

            if isinstance(node, ast.FunctionDef) and node.name == symbol_name:
                is_match = True
                kind = "function_def"
            elif isinstance(node, ast.ClassDef) and node.name == symbol_name:
                is_match = True
                kind = "class_def"
            elif isinstance(node, ast.Name) and node.id == symbol_name:
                is_match = True
                kind = "identifier"
            elif isinstance(node, ast.Attribute) and node.attr == symbol_name:
                is_match = True
                kind = "attribute_access"

            if is_match and hasattr(node, "lineno"):
                lineno = node.lineno
                snippet = lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""
                rel = str(py_file.relative_to(proj_path) if py_file.is_relative_to(proj_path) else py_file).replace("\\", "/")
                references.append({
                    "file": rel,
                    "line": lineno,
                    "kind": kind,
                    "snippet": snippet,
                })

    if not references:
        return f"No symbol references found for '{symbol_name}' in {project_dir}"

    output = [f"=== References to '{symbol_name}' ({len(references)} found) ==="]
    # Group by file
    by_file: dict[str, list[dict[str, Any]]] = {}
    for r in references:
        by_file.setdefault(r["file"], []).append(r)

    for file_path, items in sorted(by_file.items()):
        output.append(f"\n[{file_path}]")
        for item in items:
            output.append(f"  Line {item['line']} ({item['kind']}): {item['snippet']}")

    output.append("\nNote: AST search reflects static references. Dynamic getattr or runtime reflection are not traced.")
    return "\n".join(output)


def list_functions_and_classes(file_name: str) -> str:
    """
    Parse Python AST to extract all classes, functions, arguments, type annotations, and docstrings.
    """
    path = Path(file_name)
    if not path.is_file():
        return f"Error: File not found: {file_name}"

    try:
        content = _read_file_safe(path)
        tree = ast.parse(content, filename=str(path))
    except SyntaxError as e:
        return f"SyntaxError parsing {file_name}: {e}"

    classes: list[str] = []
    functions: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node) or "No docstring."
            first_line_doc = doc.strip().split("\n")[0]
            methods: list[str] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_args = [a.arg for a in item.args.args if a.arg != "self"]
                    methods.append(f"    - def {item.name}({', '.join(m_args)})")

            class_repr = f"Class {node.name} (Line {node.lineno}):\n  Doc: {first_line_doc}"
            if methods:
                class_repr += "\n  Methods:\n" + "\n".join(methods)
            classes.append(class_repr)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node) or "No docstring."
            first_line_doc = doc.strip().split("\n")[0]
            args = [a.arg for a in node.args.args]
            ret_type = ""
            if node.returns and hasattr(node.returns, "id"):
                ret_type = f" -> {node.returns.id}"
            functions.append(f"def {node.name}({', '.join(args)}){ret_type} (Line {node.lineno}):\n  Doc: {first_line_doc}")

    output = [f"=== Symbols in '{file_name}' ==="]
    if classes:
        output.append("\n-- Classes --")
        output.extend(classes)
    if functions:
        output.append("\n-- Top-level Functions --")
        output.extend(functions)

    if not classes and not functions:
        output.append("No top-level classes or functions found.")

    return "\n".join(output)


def get_file_structure(directory: str = ".") -> str:
    """
    Traverse directory and format a clean ASCII file tree.
    """
    base = Path(directory)
    if not base.is_dir():
        return f"Error: Directory not found: {directory}"

    lines: list[str] = [f"=== File Structure: {base.resolve().name} ==="]

    def _walk(cur: Path, prefix: str = ""):
        entries = sorted([p for p in cur.iterdir() if p.name not in EXCLUDED_DIRS], key=lambda x: (not x.is_dir(), x.name.lower()))
        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            child_prefix = "    " if is_last else "│   "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                _walk(entry, prefix + child_prefix)
            else:
                size_str = f" ({entry.stat().st_size} bytes)" if entry.is_file() else ""
                lines.append(f"{prefix}{connector}{entry.name}{size_str}")

    _walk(base)
    return "\n".join(lines)
