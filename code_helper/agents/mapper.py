"""
mapper.py — Architecture Mapper Worker Agent (Deterministic Plain Python, Strictly No AI).
"""

import re
from pathlib import Path
from typing import Any, AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.events import Event
from ..tools.plain_ast_tools import (
    find_imports,
    find_symbol_references,
    list_functions_and_classes,
    get_file_structure,
)
from ..tools.metrics_tool import calculate_code_metrics
from ..tools.diagram_tool import generate_architecture_diagram


STOP_WORDS = {
    "which", "what", "where", "who", "how", "does", "is", "are", "the", "a", "an",
    "in", "of", "to", "for", "from", "and", "or", "on", "calls", "call", "called",
    "imports", "import", "imported", "by", "files", "file", "symbol", "symbols",
    "reference", "references", "show", "tell", "me", "find", "list", "get", "explain",
    "function", "functions", "class", "classes", "method", "methods", "metric", "metrics",
    "loc", "lines", "code", "architecture", "structure", "project", "diagram", "graph",
}


def _find_target_file(user_query: str, project_dir: str = ".") -> str | None:
    """Dynamically find a requested file name in user query against actual project files."""
    root = Path(project_dir)
    # Check words ending with .py
    words = re.findall(r"[\w\.-]+", user_query)
    for w in words:
        if w.endswith(".py"):
            return w

    # Check against real files in the directory
    if root.exists():
        actual_files = {f.stem.lower(): f.name for f in root.glob("*.py")}
        for w in words:
            w_lower = w.lower()
            if w_lower in actual_files:
                return actual_files[w_lower]

    return None


def _find_target_symbol(user_query: str) -> str | None:
    """Dynamically extract a requested class, function, or variable identifier."""
    # 1. Quoted identifier takes precedence: 'foo' or "foo"
    quoted = re.findall(r"['\"]([A-Za-z_]\w*)['\"]", user_query)
    if quoted:
        return quoted[0]

    # 2. Look for identifier following clue keywords
    clue_match = re.search(
        r"(?:symbol|function|class|method|def|call|calls|reference|uses|used by)\s+([A-Za-z_]\w*)",
        user_query,
        re.IGNORECASE,
    )
    if clue_match:
        return clue_match.group(1)

    # 3. Look for CamelCase or snake_case identifier that isn't a stopword
    words = re.findall(r"[A-Za-z_]\w*", user_query)
    for w in words:
        if w.lower() not in STOP_WORDS and len(w) > 2:
            return w

    return None


class ArchitectureMapperAgent(BaseAgent):
    """
    Deterministic Architecture Mapper Agent.
    Subclasses BaseAgent and executes plain Python AST tools directly with ZERO LLM calls.
    Works dynamically across ANY Python codebase without hardcoded file or symbol lists.
    """
    name: str = "architecture_mapper"
    description: str = (
        "Maps project architecture, module dependencies, AST call sites, symbol references, "
        "flowchart diagrams, and file trees deterministically without using AI."
    )

    async def _run_async_impl(self, ctx: Any) -> AsyncGenerator[Event, None]:
        user_query = ""
        if hasattr(ctx, "session") and ctx.session and hasattr(ctx.session, "events"):
            for evt in reversed(ctx.session.events):
                author = getattr(evt, "author", "")
                if author == "user":
                    if hasattr(evt, "message") and evt.message:
                        user_query = str(evt.message)
                        break

        query_lower = user_query.lower()
        response_text = ""

        # 1. Diagram / flowchart intent
        if any(w in query_lower for w in ["diagram", "flowchart", "mermaid", "visual"]):
            response_text = generate_architecture_diagram(".")

        # 2. Import / dependency intent
        elif "import" in query_lower or "depend" in query_lower:
            target = _find_target_file(user_query, project_dir=".")
            if target:
                response_text = find_imports(target, project_dir=".")
            else:
                # If no specific file is mentioned, look for a module name
                target_symbol = _find_target_symbol(user_query)
                if target_symbol:
                    response_text = find_imports(target_symbol, project_dir=".")
                else:
                    # Provide an overview of imports across all root python files
                    py_files = sorted(Path(".").glob("*.py"))
                    if py_files:
                        lines = ["=== Project Module Imports Overview ==="]
                        for f in py_files[:5]:
                            lines.append(f"\n{find_imports(f.name, project_dir='.')}")
                        response_text = "\n".join(lines)
                    else:
                        response_text = "No Python files found in the current directory."

        # 3. Symbol / Reference / Who calls intent
        elif any(w in query_lower for w in ["symbol", "reference", "call", "who calls", "where is", "used"]):
            target_symbol = _find_target_symbol(user_query)
            if target_symbol:
                response_text = find_symbol_references(target_symbol, project_dir=".")
            else:
                response_text = "Please specify the function, class, or variable name you would like to trace."

        # 4. Metrics / LOC intent
        elif any(w in query_lower for w in ["metric", "loc", "lines of code", "complexity"]):
            target = _find_target_file(user_query, project_dir=".")
            if target:
                response_text = calculate_code_metrics(target)
            else:
                # Summarize metrics across all root python files
                py_files = sorted(Path(".").glob("*.py"))
                if py_files:
                    lines = ["=== Code Metrics Summary ==="]
                    for f in py_files[:6]:
                        lines.append(f"\n{calculate_code_metrics(str(f))}")
                    response_text = "\n".join(lines)
                else:
                    response_text = "No Python files found to calculate metrics."

        # 5. Functions / Classes / Signatures intent
        elif any(w in query_lower for w in ["function", "class", "signature", "def"]):
            target = _find_target_file(user_query, project_dir=".")
            if target:
                response_text = list_functions_and_classes(target)
            else:
                py_files = sorted(Path(".").glob("*.py"))
                if py_files:
                    lines = ["=== Extracted Functions & Classes ==="]
                    for f in py_files[:3]:
                        lines.append(f"\n{list_functions_and_classes(str(f))}")
                    response_text = "\n".join(lines)
                else:
                    response_text = "No Python files found to inspect."

        # 6. Default to architecture overview
        else:
            tree = get_file_structure(".")
            response_text = (
                f"=== Architecture Overview ===\n{tree}\n\n"
                "Deterministic AST tools available (Strictly 0 AI calls):\n"
                "• find_imports(target_file_or_module): Scans direct and reverse imports\n"
                "• find_symbol_references(symbol_name): Locates call sites and usages\n"
                "• list_functions_and_classes(file_name): Extracts classes, functions, and docstrings\n"
                "• calculate_code_metrics(file_path): Computes LOC, comment ratio, complexity\n"
                "• generate_architecture_diagram(): Renders Mermaid flowchart of dependencies"
            )

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            message=response_text,
        )


def create_mapper_agent() -> ArchitectureMapperAgent:
    """
    Instantiate the deterministic, non-AI Architecture Mapper agent.
    """
    return ArchitectureMapperAgent()
