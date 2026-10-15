"""
guide.py — Onboarding Guide Worker Agent (AI-Powered with Health & Run Guides).
"""

from typing import Any
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ..tools.project_summary_tool import get_project_summary
from ..tools.plain_ast_tools import get_file_structure
from ..tools.env_scanner_tool import find_env_vars
from ..tools.health_check_tool import check_system_health, get_run_commands


DEFAULT_GUIDE_INSTRUCTION = """
You are the Onboarding Guide specialist agent.
Your mission is to welcome new software engineers, explain the high-level architecture of this codebase,
outline key entrypoints (like `main.py`), and explain how to configure environment variables safely.
Always use your tools:
1. `get_project_summary` to understand total lines of code, core modules, and entrypoints.
2. `get_file_structure` to explain folder organization.
3. `find_env_vars` to explain required credentials and configuration settings in `.env`.
4. `check_system_health` to verify runtime prerequisites, `.env` keys, and core files.
5. `get_run_commands` to give exact step-by-step terminal commands to run the project.
Keep your onboarding walkthrough structured, welcoming, and actionable.
""".strip()


def create_guide_agent(
    model: Any = None,
    mock_model: bool = False,
) -> LlmAgent:
    """
    Instantiate the Onboarding Guide agent bound to codebase summary, environment, health, and run tools.
    """
    if model is None:
        model = LiteLlm(model="nvidia_nim/meta/llama-3.2-11b-vision-instruct")

    return LlmAgent(
        name="onboarding_guide",
        model=model,
        description="Assists new developers with project onboarding, directory structure, setup, health checks, and entrypoints.",
        instruction=DEFAULT_GUIDE_INSTRUCTION,
        tools=[get_project_summary, get_file_structure, find_env_vars, check_system_health, get_run_commands],
    )
