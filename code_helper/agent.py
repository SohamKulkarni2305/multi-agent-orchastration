"""
agent.py — Google ADK Root Coordinator Agent & Multi-Agent Team Assembly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from .agents.searcher import create_searcher_agent
from .agents.mapper import create_mapper_agent
from .agents.guide import create_guide_agent
from .agents.explainer import create_explainer_agent


# 1. Load environment variables from .env if present
env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

# 2. Configure NVIDIA NIM Chat Model via LiteLLM
chat_model_id = os.getenv("NVIDIA_CHAT_MODEL", "meta/llama-3.2-11b-vision-instruct").strip()
if not chat_model_id.startswith("nvidia_nim/"):
    chat_model_str = f"nvidia_nim/{chat_model_id}"
else:
    chat_model_str = chat_model_id

shared_model = LiteLlm(model=chat_model_str)

# 3. Instantiate the 4 specialized workers
searcher = create_searcher_agent(model=shared_model)
mapper = create_mapper_agent()  # Non-AI deterministic BaseAgent
guide = create_guide_agent(model=shared_model)
explainer = create_explainer_agent(model=shared_model, enable_mcp=True)

# 4. Boss Coordinator instructions
COORDINATOR_INSTRUCTION = """
You are the Boss Coordinator for the Multi-Agent Code Helper.
Your sole job is to route developer questions to the most suitable specialized worker agent:

1. 'code_searcher': For questions seeking specific functions, keywords, configuration values, constants, or code snippets across the indexed codebase.
2. 'architecture_mapper': For questions about module dependencies, imports, AST call graphs, symbol references, function signatures, or folder layout.
3. 'onboarding_guide': For new developer orientation, repo summary, setup prerequisites, entry points, or environment variable configuration.
4. 'code_explainer': For in-depth line-by-line explanations of complete files, algorithms, or complex logic.

CRITICAL INSTRUCTION:
You MUST NEVER answer substantive code or architecture questions yourself.
Always delegate directly to the single best worker agent from your sub_agents.
""".strip()

# 5. Root Agent export for Google ADK ('adk run code_helper', 'adk web')
root_agent = LlmAgent(
    name="coordinator",
    model=shared_model,
    description="Routes developer questions to the appropriate specialized code helper agent.",
    instruction=COORDINATOR_INSTRUCTION,
    sub_agents=[searcher, explainer, mapper, guide],
    tools=[],  # Boss coordinator has no direct tools; delegates exclusively to sub_agents
)
