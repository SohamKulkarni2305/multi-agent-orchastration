import pytest
from google.adk.agents import BaseAgent, LlmAgent
from code_helper.agent import root_agent

def test_root_agent_configuration():
    assert root_agent.name == "coordinator"
    assert isinstance(root_agent, LlmAgent)
    assert len(root_agent.sub_agents) == 4
    sub_agent_names = {agent.name for agent in root_agent.sub_agents}
    expected = {"code_searcher", "code_explainer", "architecture_mapper", "onboarding_guide"}
    assert sub_agent_names == expected

    # Assert exactly 1 agent does NOT use AI (architecture_mapper) and remaining 3 workers use AI
    non_ai_workers = [a for a in root_agent.sub_agents if not isinstance(a, LlmAgent) and isinstance(a, BaseAgent)]
    ai_workers = [a for a in root_agent.sub_agents if isinstance(a, LlmAgent)]
    assert len(non_ai_workers) == 1
    assert non_ai_workers[0].name == "architecture_mapper"
    assert len(ai_workers) == 3

    # Instruction must mandate delegation and forbid answering directly
    instruction = root_agent.instruction.lower()
    assert "route" in instruction or "delegate" in instruction
    assert "never answer" in instruction or "do not answer" in instruction

def test_root_agent_has_no_direct_tools():
    # Boss coordinator should only route via sub_agents and have no standalone code tools
    assert len(root_agent.tools) == 0
