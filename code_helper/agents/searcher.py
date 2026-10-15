"""
searcher.py — Code Searcher Worker Agent (AI-Powered RAG + Exact Search).
"""

from typing import Any
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ..rag.searcher import rag_search
from ..tools.search_tools import find_exact_matches


DEFAULT_SEARCHER_INSTRUCTION = """
You are the Code Searcher specialist agent.
Your mission is to find specific functions, variables, configuration constants, algorithms, or snippets in the codebase.
You have two search tools:
1. `rag_search`: For semantic retrieval against indexed codebase vectors in Pinecone.
2. `find_exact_matches`: For exact text, identifier, regex, or variable declaration lookups across files.

When providing answers:
1. Always cite exact file paths and line ranges (e.g., `config.py:L60-L75`).
2. Quote relevant lines of code accurately from retrieved context.
3. If neither search yields relevant results or the query cannot be answered from the retrieved context, you MUST respond exactly: "I could not find that".
Never hallucinate or invent code that was not retrieved.
""".strip()


def create_searcher_agent(
    model: Any = None,
    mock_model: bool = False,
) -> LlmAgent:
    """
    Instantiate the Code Searcher agent bound to custom RAG search and exact match tools.
    """
    if model is None:
        model = LiteLlm(model="nvidia_nim/meta/llama-3.2-11b-vision-instruct")

    return LlmAgent(
        name="code_searcher",
        model=model,
        description="Searches codebase for specific functions, identifiers, constants, and snippets using vector RAG and exact text matching.",
        instruction=DEFAULT_SEARCHER_INSTRUCTION,
        tools=[rag_search, find_exact_matches],
    )
