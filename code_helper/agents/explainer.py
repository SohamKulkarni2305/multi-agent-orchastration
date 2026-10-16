"""
explainer.py — Code Explainer Worker Agent (AI-Powered with Filesystem MCP + Symbol Extraction).
"""

from typing import Any
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ..tools.plain_ast_tools import list_functions_and_classes
from ..tools.metrics_tool import calculate_code_metrics
from ..tools.code_inspection_tools import get_function_source
from .mcp_setup import get_filesystem_mcp_toolset


DEFAULT_EXPLAINER_INSTRUCTION = """
You are the Code Explainer specialist agent.
Your mission is to read source code files directly, analyze their logic, and explain algorithms,
data structures, function mechanics, and architectural design choices to engineers.
Use your tools:
- Filesystem MCP tools (`read_file`, `list_directory`) to inspect whole source files.
- `get_function_source` to extract the exact source code, docstrings, and lines of a specific function or class without reading the entire file.
- `list_functions_and_classes` to get symbol overviews and docstrings.
- `calculate_code_metrics` to understand file complexity and comment ratio.
Provide clear, line-referenced, grounded explanations without hallucinating unseen code.
""".strip()


def create_explainer_agent(
    model: Any = None,
    enable_mcp: bool = True,
    mock_model: bool = False,
) -> LlmAgent:
    """
    Instantiate the Code Explainer agent bound to Filesystem MCP, source extractor, and code inspection tools.
    """
    if model is None:
        model = LiteLlm(model="nvidia_nim/meta/llama-3.2-11b-vision-instruct")

    tools: list[Any] = [get_function_source, list_functions_and_classes, calculate_code_metrics]
    if enable_mcp:
        mcp_toolset = get_filesystem_mcp_toolset(".")
        if mcp_toolset is not None:
            tools.append(mcp_toolset)

    return LlmAgent(
        name="code_explainer",
        model=model,
        description="Inspects and explains complete source code files, specific functions, and logic via Filesystem MCP and AST extraction.",
        instruction=DEFAULT_EXPLAINER_INSTRUCTION,
        tools=tools,
    )
