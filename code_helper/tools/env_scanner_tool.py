"""
env_scanner_tool.py — Scans codebase for required environment variables with secret masking.
"""

import ast
from pathlib import Path
from typing import Any


EXCLUDED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", "docs", "skills"}


def find_env_vars(project_dir: str = ".") -> str:
    """
    Scan project Python files for os.getenv and os.environ calls.
    Returns a structured report of required environment keys, reference locations,
    and safe default values, strictly masking any sensitive credentials.
    """
    root = Path(project_dir)
    if not root.is_dir():
        return f"Error: Project directory not found: {project_dir}"

    env_vars: dict[str, dict[str, Any]] = {}

    for py_file in root.rglob("*.py"):
        if set(py_file.parts).intersection(EXCLUDED_DIRS):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = py_file.read_text(encoding="latin-1", errors="replace")

        try:
            tree = ast.parse(content, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel_path = str(py_file.relative_to(root) if py_file.is_relative_to(root) else py_file).replace("\\", "/")

        for node in ast.walk(tree):
            # Check os.getenv('KEY', 'default') or os.environ.get('KEY')
            if isinstance(node, ast.Call):
                func = node.func
                is_getenv = False
                if isinstance(func, ast.Attribute) and func.attr == "getenv":
                    is_getenv = True
                elif isinstance(func, ast.Attribute) and func.attr == "get" and isinstance(func.value, ast.Attribute) and func.value.attr == "environ":
                    is_getenv = True

                if is_getenv and node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                        var_name = first_arg.value
                        default_val = "None"
                        if len(node.args) > 1:
                            second_arg = node.args[1]
                            if isinstance(second_arg, ast.Constant):
                                default_val = str(second_arg.value)

                        # Mask default if it looks like a sensitive key
                        if any(s in var_name.upper() for s in ["KEY", "SECRET", "PASSWORD", "TOKEN"]):
                            if default_val not in ("None", "", "default_tok"):
                                default_val = "***MASKED***"

                        record = env_vars.setdefault(var_name, {"files": set(), "defaults": set()})
                        record["files"].add(f"{rel_path}:{node.lineno}")
                        if default_val:
                            record["defaults"].add(default_val)

            # Check os.environ['KEY']
            elif isinstance(node, ast.Subscript):
                val = node.value
                if isinstance(val, ast.Attribute) and val.attr == "environ":
                    slice_node = node.slice
                    if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, str):
                        var_name = slice_node.value
                        record = env_vars.setdefault(var_name, {"files": set(), "defaults": set()})
                        record["files"].add(f"{rel_path}:{node.lineno}")

    if not env_vars:
        return f"No environment variables detected in {project_dir}"

    output = [
        f"=== Detected Environment Variables ({len(env_vars)} found) ===",
        "Security Notice: Actual environment secrets are never printed; only variable names and safe defaults are reported.\n",
    ]

    for var_name, data in sorted(env_vars.items()):
        files_str = ", ".join(sorted(data["files"]))
        defs_str = ", ".join(sorted(data["defaults"])) if data["defaults"] else "None (Required)"
        output.append(f"• {var_name}")
        output.append(f"    Default Value : {defs_str}")
        output.append(f"    Referenced In : {files_str}")

    return "\n".join(output)
