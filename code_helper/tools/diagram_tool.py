"""
diagram_tool.py — Deterministic Mermaid Architecture Diagram Generator.
Supports:
1. Whole-project architecture overview diagrams.
2. File-centric deep architecture diagrams (classes, methods, internal function call graph, upstream callers, downstream dependencies, external APIs).
"""

import ast
import os
import re
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
    "skills",
}


def _get_valid_python_files(root: Path) -> list[Path]:
    """Return all non-venv python files under root rapidly by pruning excluded directories."""
    valid_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # In-place directory pruning so os.walk skips .venv, venv, .git completely
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".py"):
                p = Path(dirpath) / fn
                parts = set(p.parts)
                if "uploads" in parts and not root.name.startswith("current_codebase") and not str(root).endswith("uploads"):
                    continue
                valid_files.append(p)
    return sorted(valid_files)


def safe_node_id(name: str) -> str:
    """Sanitize string into a safe Mermaid node identifier."""
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    return f"n_{clean}"


def generate_file_architecture_diagram(file_identifier: str, project_dir: str = ".") -> str:
    """
    Generate a detailed file-centric architecture flowchart for a specific Python file.
    Traces:
    - Target file's classes and methods
    - Target file's functions and internal call flow
    - Upstream callers (modules that import/call this file)
    - Downstream dependencies (internal modules imported by this file)
    - External packages & APIs used
    """
    root = Path(project_dir).resolve()
    valid_files = _get_valid_python_files(root)

    # Locate target file
    target_clean = file_identifier.strip().lower()
    target_stem = target_clean[:-3] if target_clean.endswith(".py") else target_clean

    target_path: Path | None = None
    for f in valid_files:
        if (
            f.name.lower() == target_clean
            or f.name.lower() == f"{target_stem}.py"
            or f.stem.lower() == target_stem
            or str(f).replace("\\", "/").lower().endswith(target_clean)
        ):
            target_path = f
            break

    if not target_path or not target_path.exists():
        # Fallback to finding by exact name in root
        direct = root / file_identifier
        if direct.exists() and direct.is_file():
            target_path = direct
        else:
            return f"Error: Target file '{file_identifier}' was not found in active codebase."

    code = target_path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(code)
    except Exception as e:
        return f"Error parsing AST for `{target_path.name}`: {e}"

    # 1. Parse Target File Internals
    local_funcs: list[str] = []
    local_classes: dict[str, list[str]] = {}
    func_calls: list[tuple[str, str]] = []  # (caller, callee)
    downstream_imports: dict[str, list[str]] = {}  # {module_name: [imported_symbols]}
    external_imports: list[str] = []

    project_stems = {f.stem: f for f in valid_files}

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fname = node.name
            if not fname.startswith("__"):
                local_funcs.append(fname)
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call):
                        if isinstance(sub.func, ast.Name):
                            called_name = sub.func.id
                            func_calls.append((fname, called_name))
        elif isinstance(node, ast.ClassDef):
            cname = node.name
            methods: list[str] = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("__"):
                        methods.append(item.name)
            local_classes[cname] = methods
        elif isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".")[0]
                if base in project_stems and project_stems[base] != target_path:
                    downstream_imports.setdefault(project_stems[base].name, []).append(alias.name)
                elif base not in ("sys", "typing", "pathlib", "os"):
                    external_imports.append(base)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base = node.module.split(".")[0]
                syms = [a.name for a in node.names]
                if base in project_stems and project_stems[base] != target_path:
                    downstream_imports.setdefault(project_stems[base].name, []).extend(syms)
                elif base not in ("sys", "typing", "pathlib", "os"):
                    external_imports.append(base)

    # Filter internal calls to only those calling other local functions
    internal_calls = [(c, t) for (c, t) in func_calls if t in local_funcs and c != t]
    unique_internal_calls = sorted(set(internal_calls))

    # 2. Scan Upstream Callers across the codebase
    upstream_callers: dict[str, list[str]] = {}  # {caller_file: [imported_symbols]}
    for f in valid_files:
        if f == target_path:
            continue
        try:
            f_code = f.read_text(encoding="utf-8", errors="replace")
            f_tree = ast.parse(f_code)
            for node in ast.walk(f_tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == target_path.stem or alias.name.startswith(f"{target_path.stem}."):
                            upstream_callers.setdefault(f.name, []).append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and (node.module == target_path.stem or node.module.endswith(f".{target_path.stem}")):
                        syms = [a.name for a in node.names]
                        upstream_callers.setdefault(f.name, []).extend(syms)
        except Exception:
            continue

    # 3. Construct Mermaid Flowchart
    lines = [
        "```mermaid",
        "graph TD",
        f"    %% Dedicated Architecture Flowchart for {target_path.name}",
    ]

    # Subgraph 1: Upstream Callers
    if upstream_callers:
        lines.append('    subgraph Subgraph_Upstream["⬆️ Upstream Callers (Who Imports This File)"]')
        for caller, syms in upstream_callers.items():
            cid = safe_node_id("caller_" + caller)
            label = f"<b>{caller}</b>"
            lines.append(f'        {cid}["{label}"]')
        lines.append("    end")

    # Subgraph 2: Core File Details (Classes & Functions)
    target_id = safe_node_id("core_" + target_path.name)
    lines.append(f'    subgraph Subgraph_Core["🎯 Target Module: {target_path.name}"]')
    lines.append("        direction TB")

    # Add Class Nodes
    for cname, methods in local_classes.items():
        clid = safe_node_id(f"cls_{cname}")
        m_str = ("<br/>Methods: " + ", ".join(methods[:4])) if methods else ""
        lines.append(f'        {clid}["class <b>{cname}</b>{m_str}"]')

    # Add Function Nodes
    for fn in local_funcs:
        fnid = safe_node_id(f"fn_{fn}")
        lines.append(f'        {fnid}["def <b>{fn}()</b>"]')

    # If file has neither classes nor functions, show file node
    if not local_classes and not local_funcs:
        lines.append(f'        {target_id}["<b>{target_path.name}</b><br/>(Script / Module)"]')

    # Add internal call links between functions
    if unique_internal_calls:
        for caller, callee in unique_internal_calls:
            lines.append(f"        {safe_node_id('fn_' + caller)} -->|\"calls\"| {safe_node_id('fn_' + callee)}")

    lines.append("    end")

    # Subgraph 3: Downstream Project Dependencies
    if downstream_imports:
        lines.append('    subgraph Subgraph_Downstream["⬇️ Downstream Dependencies (Imported Modules)"]')
        for dep, syms in downstream_imports.items():
            did = safe_node_id("dep_" + dep)
            s_label = ("<br/>(" + ", ".join(syms[:3]) + ")") if syms else ""
            lines.append(f'        {did}["<b>{dep}</b>{s_label}"]')
        lines.append("    end")

    # Subgraph 4: External Services / Libraries
    ext_unique = sorted(set(external_imports))
    if ext_unique:
        lines.append('    subgraph Subgraph_External["📦 External Libraries & APIs"]')
        for ext in ext_unique[:5]:
            eid = safe_node_id("ext_" + ext)
            lines.append(f'        {eid}["📦 <b>{ext}</b>"]')
        lines.append("    end")

    # Connect Upstream Callers to Core File functions or module
    first_target_node = (
        safe_node_id(f"cls_{list(local_classes.keys())[0]}")
        if local_classes
        else (safe_node_id(f"fn_{local_funcs[0]}") if local_funcs else target_id)
    )

    for caller, syms in upstream_callers.items():
        cid = safe_node_id("caller_" + caller)
        matched_target = None
        for s in syms:
            if s in local_funcs:
                matched_target = safe_node_id(f"fn_{s}")
                break
            elif s in local_classes:
                matched_target = safe_node_id(f"cls_{s}")
                break
        t_node = matched_target or first_target_node
        label = (", ".join(syms[:2])) if syms else "imports"
        lines.append(f'    {cid} ==>|"{label}"| {t_node}')

    # Connect Core File to Downstream Dependencies
    last_source_node = (
        safe_node_id(f"fn_{local_funcs[-1]}")
        if local_funcs
        else (safe_node_id(f"cls_{list(local_classes.keys())[-1]}") if local_classes else target_id)
    )

    for dep, syms in downstream_imports.items():
        did = safe_node_id("dep_" + dep)
        s_text = (", ".join(syms[:2])) if syms else "imports"
        lines.append(f'    {last_source_node} -->|"{s_text}"| {did}')

    # Connect to External APIs
    for ext in ext_unique[:3]:
        eid = safe_node_id("ext_" + ext)
        lines.append(f'    {first_target_node} -.->|"uses"| {eid}')

    lines.append("```")

    desc = (
        f"=== Architecture Diagram for `{target_path.name}` ===\n\n"
        + "\n".join(lines)
        + f"\n\n*File-centric AST analysis: {len(local_classes)} classes, {len(local_funcs)} functions, "
        f"{len(upstream_callers)} upstream callers, {len(downstream_imports)} downstream imports.*"
    )
    return desc


def generate_architecture_diagram(project_dir: str = ".", target_file: str | None = None) -> str:
    """
    Generate a clean, valid Mermaid flowchart diagram (graph TD).
    If target_file is provided: generates a dedicated file-centric architecture diagram.
    If target_file is None: generates a comprehensive project-wide architecture diagram.
    """
    root = Path(project_dir).resolve()
    if not root.exists():
        return f"Error: Project directory '{project_dir}' not found."

    # If target_file is specified, route to file-centric generator
    if target_file and target_file.strip():
        return generate_file_architecture_diagram(target_file, project_dir=str(root))

    # Otherwise generate project-wide architecture overview
    valid_files = _get_valid_python_files(root)
    if not valid_files:
        return "No valid Python files found to diagram."

    # If there are more than 15 files, prioritize root and primary pipeline files
    display_files = valid_files
    if len(valid_files) > 15:
        root_files = [f for f in valid_files if f.parent == root]
        if len(root_files) >= 4:
            display_files = root_files
        else:
            display_files = valid_files[:15]

    edges: list[tuple[str, str, str]] = []
    file_stems = {f.stem: f for f in display_files}
    file_details: dict[str, dict[str, list[str]]] = {}

    for f in display_files:
        try:
            rel_name = str(f.relative_to(root)).replace("\\", "/")
        except ValueError:
            rel_name = f.name

        file_details[f.name] = {"classes": [], "functions": [], "rel": rel_name}

        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    file_details[f.name]["classes"].append(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    file_details[f.name]["functions"].append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    base = alias.name.split(".")[0]
                    if base in file_stems and file_stems[base] != f:
                        target = file_stems[base].name
                        edges.append((f.name, target, "imports"))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base = node.module.split(".")[0]
                    if base in file_stems and file_stems[base] != f:
                        target = file_stems[base].name
                        names = ", ".join(a.name for a in node.names[:2])
                        edges.append((f.name, target, names or "imports"))

    unique_edges = sorted(set(edges))
    lines = [
        "```mermaid",
        "graph TD",
        "    %% Core Component Nodes",
    ]

    for f in display_files:
        nid = safe_node_id(f.name)
        details = file_details.get(f.name, {"classes": [], "functions": [], "rel": f.name})
        cls_list = details["classes"][:2]
        fn_list = details["functions"][:3]

        label_parts = [f"<b>{f.name}</b>"]
        if cls_list:
            label_parts.append("Classes: " + ", ".join(cls_list))
        if fn_list:
            label_parts.append("Funcs: " + ", ".join(fn_list))

        node_label = "<br/>".join(label_parts)
        lines.append(f'    {nid}["{node_label}"]')

    lines.append("    %% Dependency Edges")
    if unique_edges:
        for src, dst, label in unique_edges:
            src_id = safe_node_id(src)
            dst_id = safe_node_id(dst)
            lines.append(f'    {src_id} -->|"{label}"| {dst_id}')
    else:
        for i in range(len(display_files) - 1):
            s_id = safe_node_id(display_files[i].name)
            t_id = safe_node_id(display_files[i + 1].name)
            lines.append(f'    {s_id} -.- {t_id}')

    lines.append("```")

    explanation = (
        "=== Architecture Dependency Diagram (Mermaid) ===\n\n"
        + "\n".join(lines)
        + f"\n\n*Analyzed {len(display_files)} source files in '{root.name}' with {len(unique_edges)} module connections.*"
    )
    return explanation
