import pytest
from pathlib import Path
from google.adk.agents import BaseAgent, LlmAgent
from code_helper.agent import root_agent
from code_helper.rag.searcher import rag_search

def test_readme_contains_required_student_guide_sections():
    readme_path = Path("README.md")
    assert readme_path.is_file(), "README.md must exist in repository root"
    content = readme_path.read_text(encoding="utf-8")
    
    assert "Table of Agents" in content or "| Agent" in content
    assert "Table of Tools" in content or "| Tool" in content
    assert "Chunk Size Evaluation" in content or "200" in content
    assert "MCP Server" in content or "Model Context Protocol" in content
    assert "Sample Questions" in content or "Sample Question 1" in content
    assert "Problem Encountered" in content or "Troubleshooting" in content
    assert "adk run code_helper" in content

def test_coordinator_agent_hierarchy_and_non_ai():
    assert root_agent.name == "coordinator"
    assert isinstance(root_agent, LlmAgent)
    assert len(root_agent.sub_agents) == 4

    non_ai_workers = [a for a in root_agent.sub_agents if not isinstance(a, LlmAgent) and isinstance(a, BaseAgent)]
    ai_workers = [a for a in root_agent.sub_agents if isinstance(a, LlmAgent)]
    assert len(non_ai_workers) == 1
    assert non_ai_workers[0].name == "architecture_mapper"
    assert len(ai_workers) == 3

def test_searcher_exact_fallback_string():
    res = rag_search("xyznonexistenttopic999", top_k=3, threshold=0.8, mock=True)
    assert res.strip() == "I could not find that"
