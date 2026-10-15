import pytest
from pathlib import Path
from google.adk.agents import BaseAgent, LlmAgent
from code_helper.agents.searcher import create_searcher_agent
from code_helper.agents.mapper import create_mapper_agent
from code_helper.agents.guide import create_guide_agent
from code_helper.agents.explainer import create_explainer_agent
from code_helper.agents.mcp_setup import build_mcp_server_params

def test_agent_hierarchy_and_ai_vs_non_ai():
    searcher = create_searcher_agent(mock_model=True)
    mapper = create_mapper_agent()
    guide = create_guide_agent(mock_model=True)
    explainer = create_explainer_agent(mock_model=True, enable_mcp=False)

    assert searcher.name == "code_searcher"
    assert mapper.name == "architecture_mapper"
    assert guide.name == "onboarding_guide"
    assert explainer.name == "code_explainer"

    # Exactly 1 agent must NOT use AI (architecture_mapper is a BaseAgent without an LLM model)
    assert not isinstance(mapper, LlmAgent)
    assert isinstance(mapper, BaseAgent)
    assert isinstance(searcher, LlmAgent)
    assert isinstance(guide, LlmAgent)
    assert isinstance(explainer, LlmAgent)

    assert len(searcher.tools) >= 1
    assert len(guide.tools) >= 3  # summary, structure, env vars
    assert len(explainer.tools) >= 2
    assert "I could not find that" in searcher.instruction

def test_mcp_config_resolution():
    params = build_mcp_server_params(".")
    assert params.command == "npx"
    assert "@modelcontextprotocol/server-filesystem" in params.args
    assert Path(params.args[-1]).is_absolute()
