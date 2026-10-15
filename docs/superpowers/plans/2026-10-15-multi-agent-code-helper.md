# Multi-Agent Code Helper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a hierarchical multi-agent code assistant consisting of 1 Boss coordinator and 4 specialized workers (Code Searcher, Code Explainer, Architecture Mapper, Onboarding Guide) using Google ADK, LiteLLM with NVIDIA NIM, Pinecone vector search, custom RAG (no LangChain/LlamaIndex), and a Filesystem MCP server to index and assist developers on the Naive RAG repository.

**Architecture:** A hierarchical multi-agent system built on `google.adk`. Exactly 1 agent operates without AI (`architecture_mapper` as a deterministic `BaseAgent` parsing ASTs directly with zero LLM calls), while the remaining 4 agents use AI: the root agent (`coordinator` routing questions via `LiteLlm`), Code Searcher (`LlmAgent` querying Pinecone embeddings via custom 5-step RAG), Code Explainer (`LlmAgent` inspecting source files via `@modelcontextprotocol/server-filesystem`), and Onboarding Guide (`LlmAgent` synthesizing project structure into clear onboarding guides).

**Tech Stack:** Python 3.10+, `google-adk` (v2.12.0), `litellm` (v1.105.1), `pinecone` (v10.0.0), `openai` (v2.54.0 for NVIDIA NIM OpenAI-compatible API), `mcp` (v2.3.0), `python-dotenv` (v1.2.4), Node.js / `npx @modelcontextprotocol/server-filesystem`, `pytest` (v9.1.1).

**Spec:** Multi-Agent Code Helper Student Guide (deboistech, 2026-10-13) covering 5-agent team, 5+ custom tools, custom 5-step RAG pipeline, Pinecone serverless index (dim 2048, cosine), NVIDIA Nemotron embeddings, and Filesystem MCP integration operating over the cloned `Naive_RAG` repository.

## Global Constraints

- Never commit secrets or API keys to git or hardcode in code; load all credentials exclusively from `.env`.
- Do not use LlamaIndex or LangChain for RAG; implement all 5 RAG steps (Read, Split, Embed, Store, Search) directly in plain Python.
- Pinecone index dimension must be exactly `2048` with `cosine` metric for `nvidia/nemotron-3-embed-1b`.
- Provide at least 5 custom tools (excluding external MCP tools). This plan provides 8 custom tools (7 deterministic plain Python tools + 1 custom RAG search tool).
- Exactly 1 agent must NOT use AI (`architecture_mapper` as a deterministic `BaseAgent` executing standard library `ast` parsing without an LLM); the other 4 agents use AI models.
- Boss coordinator must strictly route questions to workers and never answer substantive code questions directly.
- Missing or insufficient retrieval evidence must produce the exact fallback response: `I could not find that`.
- Target codebase to index is the original repository source files (`config.py`, `indexer.py`, `vector_store.py`, `query_pipeline.py`, `main.py`, `data/*.txt`), explicitly excluding `code_helper/`, `tests/`, `.venv/`, `.git/`, `docs/`, and `__pycache__/`.
- Codebase must match Google ADK layout conventions: `code_helper/__init__.py` and `code_helper/agent.py` exporting `root_agent`.
- All filesystem operations and path resolution must be cross-platform and handle Windows drive letters and separators safely via `pathlib.Path`.

## Review Focus

1. **Missing or invalid API keys during unit testing:** Custom RAG embedder, Pinecone client, and agents must feature a mock/dry-run mode so unit tests run completely offline without active NVIDIA NIM or Pinecone network credentials.
2. **Zero semantic hallucination on fallback:** When search yields no chunks or similarity score is below the configured threshold (default 0.45), Code Searcher and `rag_search` must strictly return `"I could not find that"`.
3. **Deterministic non-AI Architecture Mapper:** `architecture_mapper` must subclass `google.adk.agents.BaseAgent`, override `_run_async_impl`, and yield verified AST output directly via `Event(message=...)` without passing through any LLM or incurring API token usage.
4. **Safe Filesystem MCP configuration on Windows:** `code_helper/agents/mcp_setup.py` must resolve the repository root to an absolute path (`Path(target_dir).resolve()`), normalize slashes, and configure `McpToolset` without launching live subprocesses during standard unit tests.
5. **AST parsing resilience:** Deterministic tools must catch `SyntaxError`, `UnicodeDecodeError`, and `FileNotFoundError` gracefully, returning descriptive human-readable errors instead of unhandled tracebacks. Secret values in `.env` or code must never be printed by the environment scanner.

---

### Task 1: Custom RAG Pipeline for Codebase Indexing & Search

**Files:**
- Create: `code_helper/rag/__init__.py`
- Create: `code_helper/rag/chunker.py`
- Create: `code_helper/rag/embedder.py`
- Create: `code_helper/rag/pinecone_client.py`
- Create: `code_helper/rag/searcher.py`
- Test: `tests/test_rag_pipeline.py`

**Interfaces:**
- Consumes: Target files (`config.py`, `indexer.py`, etc.), `.env` settings (`NVIDIA_API_KEY`, `PINECONE_API_KEY`, `NVIDIA_BASE_URL`).
- Produces:
  - `chunker.chunk_file(file_path: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]`: Line-aware splitting with metadata (`chunk_id`, `file_path`, `start_line`, `end_line`, `text`).
  - `chunker.evaluate_chunk_sizes(target_dir: str, sizes: list[int] = [200, 500], eval_queries: list[dict] = None) -> dict`: Compares chunk distributions and retrieval recall on benchmark queries.
  - `embedder.get_embeddings(texts: list[str], input_type: str = "passage", mock: bool = False) -> list[list[float]]`: Direct call to NVIDIA NIM `nvidia/nemotron-3-embed-1b` with `extra_body={"input_type": input_type, "truncate": "END"}`. Validates exact 2048 dimensions. Deterministic mock vector generation for offline tests.
  - `pinecone_client.ensure_pinecone_index(index_name: str, dimension: int = 2048, metric: str = "cosine", mock: bool = False)`: Idempotently creates index and awaits status readiness.
  - `pinecone_client.sync_chunks_to_pinecone(chunks: list[dict], index_name: str, batch_size: int = 50, mock: bool = False) -> int`: Batched upserts with deterministic chunk IDs (`{file_rel}:chunk_{idx}:{start_line}_{end_line}`). Supports vector cleanup on re-indexing.
  - `searcher.rag_search(query: str, top_k: int = 3, threshold: float = 0.45, mock: bool = False) -> str`: Embeds query with `input_type="query"`, searches Pinecone, and returns formatted passages with file and line citations or `"I could not find that"`.

- [x] **Step 1: Write isolated unit tests using synthetic fixtures for chunker, embedder, and searcher**

```python
# tests/test_rag_pipeline.py
import pytest
from pathlib import Path
from code_helper.rag.chunker import chunk_file, evaluate_chunk_sizes
from code_helper.rag.embedder import get_embeddings
from code_helper.rag.searcher import rag_search

@pytest.fixture
def sample_code_file(tmp_path):
    f = tmp_path / "sample.py"
    f.write_text(
        "import os\n\ndef add(a: int, b: int) -> int:\n    '''Add two numbers.'''\n    return a + b\n\n"
        "def subtract(a: int, b: int) -> int:\n    '''Subtract two numbers.'''\n    return a - b\n",
        encoding="utf-8"
    )
    return str(f)

def test_chunk_file_metadata_and_lines(sample_code_file):
    chunks = chunk_file(sample_code_file, chunk_size=80, overlap=20)
    assert len(chunks) > 0
    first = chunks[0]
    assert "chunk_id" in first
    assert "file_path" in first
    assert "start_line" in first
    assert "end_line" in first
    assert first["start_line"] >= 1
    assert first["end_line"] >= first["start_line"]

def test_embedder_dimension_and_mock():
    # Offline unit test: verifies exact 2048 dimensions without live API
    vecs = get_embeddings(["def test_fn(): pass"], input_type="passage", mock=True)
    assert len(vecs) == 1
    assert len(vecs[0]) == 2048
    assert all(isinstance(x, float) for x in vecs[0])

def test_searcher_fallback_on_unrelated_query():
    # Irrelevant query should trigger low similarity and return fallback string
    result = rag_search("totally unrelated xyz 123", top_k=3, threshold=0.9, mock=True)
    assert result.strip() == "I could not find that"

def test_evaluate_chunk_sizes_benchmark(sample_code_file, tmp_path):
    res = evaluate_chunk_sizes(str(tmp_path), sizes=[50, 150])
    assert 50 in res
    assert 150 in res
    assert "chunk_count" in res[50]
    assert "avg_chars" in res[50]
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_rag_pipeline.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'code_helper'`

- [x] **Step 3: Implement custom RAG pipeline modules**

- `code_helper/rag/__init__.py`: Clean module exports.
- `code_helper/rag/chunker.py`:
  - `chunk_file(file_path, chunk_size=500, overlap=50)`: Line-preserving sliding window. Calculates line numbers by tracking newline offsets.
  - `evaluate_chunk_sizes(target_dir, sizes=[200, 500], eval_queries=None)`: Evaluates chunk distributions and runs benchmark queries against index chunks to calculate recall rates.
- `code_helper/rag/embedder.py`:
  - Implements `get_embeddings(texts, input_type="passage", mock=False)`.
  - Live mode: Calls NVIDIA NIM endpoint via `openai.OpenAI(base_url=..., api_key=...)` with `model="nvidia/nemotron-3-embed-1b"` and `extra_body={"input_type": input_type, "truncate": "END"}`.
  - Validates `len(vec) == 2048` before returning.
  - Mock mode: Deterministic hashing returning unit-normalized 2048-dim float vectors.
- `code_helper/rag/pinecone_client.py`:
  - `ensure_pinecone_index`: Checks `client.list_indexes()` by name; creates `ServerlessSpec` with `dimension=2048, metric="cosine"`. Awaits ready status via `client.describe_index(name).status['ready']`.
  - `sync_chunks_to_pinecone`: Deterministic chunk IDs `{file_rel}:chunk_{idx}:{start_line}_{end_line}`. Batched in groups of 50 chunks. Supports optional index vector clearing before upserting.
- `code_helper/rag/searcher.py`:
  - `rag_search(query, top_k=3, threshold=0.45, mock=False)`: Embeds query with `input_type="query"`, retrieves top-k vectors from Pinecone. Filters matches by `score >= threshold`. Formats citations (`file_path:start_line-end_line`). If no matches pass threshold, returns exactly `"I could not find that"`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_rag_pipeline.py -v`
Expected: PASS

- [x] **Step 5: Verify integration with existing Naive_RAG files**

Run a sanity check script testing `chunk_file("config.py")` to ensure real repo source code chunks cleanly.

---

### Task 2: Deterministic Plain Python Architecture & Inspection Tools (7 Tools)

**Files:**
- Create: `code_helper/tools/__init__.py`
- Create: `code_helper/tools/plain_ast_tools.py`
- Create: `code_helper/tools/project_summary_tool.py`
- Create: `code_helper/tools/env_scanner_tool.py`
- Create: `code_helper/tools/metrics_tool.py`
- Test: `tests/test_plain_tools.py`

**Interfaces:**
- Consumes: Target directory path (`.` by default) and source files (`config.py`, `indexer.py`, `main.py`, etc.).
- Produces 7 deterministic plain Python tools (with `rag_search` forming 8 custom tools total):
  - `find_imports(target_file_or_module: str, project_dir: str = ".") -> str`: Parses ASTs to show what a file imports and scans other files to show which files import a given module.
  - `find_symbol_references(symbol_name: str, project_dir: str = ".") -> str`: Scans ASTs across the project to locate all usages and call sites of a class or function.
  - `list_functions_and_classes(file_name: str) -> str`: Parses Python AST to extract classes, functions, arguments, return type annotations, and docstrings.
  - `get_file_structure(directory: str = ".") -> str`: Directory tree traversal returning hierarchical layout, skipping git/virtualenv folders.
  - `get_project_summary(directory: str = ".") -> str`: Analyzes project entry points, total lines of code, and module summaries.
  - `find_env_vars(project_dir: str = ".") -> str`: Scans all Python files for `os.getenv` calls, `.env` references, and environment configuration keys with defaults, strictly masking secrets.
  - `calculate_code_metrics(file_path: str) -> str`: Computes total lines, code lines, comment lines, blank lines, function/class counts, and docstring coverage.

- [x] **Step 1: Write failing tests for AST, env scanner, metrics, and plain tools using temporary synthetic files**

```python
# tests/test_plain_tools.py
import pytest
from pathlib import Path
from code_helper.tools.plain_ast_tools import (
    find_imports,
    find_symbol_references,
    list_functions_and_classes,
    get_file_structure,
)
from code_helper.tools.project_summary_tool import get_project_summary
from code_helper.tools.env_scanner_tool import find_env_vars
from code_helper.tools.metrics_tool import calculate_code_metrics

@pytest.fixture
def mock_repo(tmp_path):
    sub = tmp_path / "pkg"
    sub.mkdir()
    f1 = sub / "module_a.py"
    f1.write_text(
        "import os\n\ndef helper():\n    '''A helper docstring.'''\n    key = os.getenv('SECRET_TOKEN', 'default_tok')\n    return key\n",
        encoding="utf-8"
    )
    f2 = sub / "module_b.py"
    f2.write_text(
        "from .module_a import helper\n\nclass Runner:\n    def run(self):\n        return helper()\n",
        encoding="utf-8"
    )
    return str(tmp_path)

def test_find_imports_and_references(mock_repo):
    mod_b = str(Path(mock_repo) / "pkg" / "module_b.py")
    imports = find_imports(mod_b, project_dir=mock_repo)
    assert "module_a" in imports

    refs = find_symbol_references("helper", project_dir=mock_repo)
    assert "module_b.py" in refs

def test_list_functions_and_classes(mock_repo):
    mod_b = str(Path(mock_repo) / "pkg" / "module_b.py")
    symbols = list_functions_and_classes(mod_b)
    assert "Runner" in symbols
    assert "run" in symbols

def test_env_scanner_masks_secrets(mock_repo):
    env_info = find_env_vars(mock_repo)
    assert "SECRET_TOKEN" in env_info
    # Real secrets must never be leaked; safe defaults or masked placeholders
    assert "default_tok" in env_info or "masked" in env_info.lower()

def test_calculate_code_metrics(mock_repo):
    mod_a = str(Path(mock_repo) / "pkg" / "module_a.py")
    metrics = calculate_code_metrics(mod_a)
    assert "Lines of Code" in metrics
    assert "Functions" in metrics

def test_ast_error_handling(tmp_path):
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken_syntax(:\n pass", encoding="utf-8")
    result = list_functions_and_classes(str(bad_file))
    assert "Error" in result or "SyntaxError" in result
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_plain_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'code_helper.tools'`

- [x] **Step 3: Implement plain AST, env scanner, metrics, and project analysis tools**

- `code_helper/tools/__init__.py`: Clean exports of all 7 tools.
- `code_helper/tools/plain_ast_tools.py`:
  - `find_imports`: Parses AST `Import` and `ImportFrom`. Handles single file inspects and project-wide reverse import lookups. Catches `SyntaxError` and `FileNotFoundError`.
  - `find_symbol_references`: Scans AST for `ast.Name(id=symbol)` and `ast.Attribute(attr=symbol)`. Notes limitations regarding dynamic reflection.
  - `list_functions_and_classes`: Extracts classes, methods, functions, type hints, and docstrings.
  - `get_file_structure`: Traverses project ignoring `.git`, `__pycache__`, `.venv`, `tests`, `docs`, `skills`.
- `code_helper/tools/project_summary_tool.py`:
  - `get_project_summary`: Returns LOC, entry points (`main.py`), and high-level module purposes.
- `code_helper/tools/env_scanner_tool.py`:
  - `find_env_vars`: Scans AST for `os.getenv` calls, `.env` lookups, and dataclass config patterns. Masks values to prevent credential leakage.
- `code_helper/tools/metrics_tool.py`:
  - `calculate_code_metrics`: Calculates lines of code, comments, blank lines, function count, class count, and docstring coverage percentage.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_plain_tools.py -v`
Expected: PASS

---

### Task 3: Specialized Worker Agents & MCP Filesystem Integration

**Files:**
- Create: `code_helper/agents/__init__.py`
- Create: `code_helper/agents/mcp_setup.py`
- Create: `code_helper/agents/searcher.py`
- Create: `code_helper/agents/mapper.py`
- Create: `code_helper/agents/guide.py`
- Create: `code_helper/agents/explainer.py`
- Test: `tests/test_agents.py`

**Interfaces:**
- Consumes:
  - Custom RAG tool (`rag_search`)
  - Plain Python tools (`find_imports`, `find_symbol_references`, `list_functions_and_classes`, `get_file_structure`, `get_project_summary`, `find_env_vars`, `calculate_code_metrics`)
  - `google.adk.agents.BaseAgent`, `google.adk.agents.LlmAgent`, `google.adk.models.lite_llm.LiteLlm`, `google.adk.tools.McpToolset`, `mcp.StdioServerParameters`
- Produces:
  - `create_searcher_agent(model=None)`: `LlmAgent` (uses AI) bound to `rag_search` with strict instruction to cite file and lines, and respond `"I could not find that"` on missing evidence.
  - `create_mapper_agent()`: `BaseAgent` (**does NOT use AI**; 100% deterministic) executing AST tools (`find_imports`, `find_symbol_references`, `list_functions_and_classes`, `calculate_code_metrics`, `get_file_structure`) and yielding verified findings directly without an LLM.
  - `create_guide_agent(model=None)`: `LlmAgent` (uses AI) bound to `get_project_summary`, `get_file_structure`, and `find_env_vars` for developer onboarding.
  - `create_explainer_agent(model=None, enable_mcp=True)`: `LlmAgent` (uses AI) bound to MCP Filesystem server (`read_file`, `list_directory`), `list_functions_and_classes`, and `calculate_code_metrics`.
  - `get_filesystem_mcp_toolset(target_dir=".")`: Configures `McpToolset` using `StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", str(Path(target_dir).resolve())])`.

- [x] **Step 1: Write failing test verifying worker configurations, models, and tools**

```python
# tests/test_agents.py
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
    assert len(guide.tools) >= 3
    assert "I could not find that" in searcher.instruction

def test_mcp_config_resolution():
    params = build_mcp_server_params(".")
    assert params.command == "npx"
    assert "@modelcontextprotocol/server-filesystem" in params.args
    assert Path(params.args[-1]).is_absolute()
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_agents.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'code_helper.agents'`

- [x] **Step 3: Implement worker agents and MCP configuration**

- `code_helper/agents/__init__.py`: Package exports.
- `code_helper/agents/mcp_setup.py`:
  - `build_mcp_server_params(target_dir=".")`: Returns `StdioServerParameters(command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", str(Path(target_dir).resolve())])`.
  - `get_filesystem_mcp_toolset(target_dir=".")`: Instantiates `McpToolset(connection_params=build_mcp_server_params(target_dir), tool_filter=["read_file", "list_directory"])`.
- `code_helper/agents/searcher.py`:
  - `code_searcher` (`LlmAgent`, uses AI). Bound to `rag_search`. Prompt requires citing exact filenames and line numbers, and responding with `"I could not find that"` on missing results.
- `code_helper/agents/mapper.py`:
  - `ArchitectureMapperAgent` subclassing `BaseAgent` (**strictly NO AI**). Implements `async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:` to inspect user queries, invoke deterministic AST tools, and yield the structured response directly as `Event(message=...)`.
- `code_helper/agents/guide.py`:
  - `onboarding_guide` (`LlmAgent`, uses AI). Bound to `get_project_summary`, `get_file_structure`, `find_env_vars`.
- `code_helper/agents/explainer.py`:
  - `code_explainer` (`LlmAgent`, uses AI). Bound to Filesystem MCP tools, `list_functions_and_classes`, and `calculate_code_metrics`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_agents.py -v`
Expected: PASS

---

### Task 4: Boss Coordinator Agent & Google ADK Package Entrypoint

**Files:**
- Create: `code_helper/__init__.py`
- Create: `code_helper/agent.py`
- Test: `tests/test_coordinator.py`

**Interfaces:**
- Consumes: The 4 worker sub-agents (`code_searcher`, `code_explainer`, `architecture_mapper`, `onboarding_guide`), `google.adk.models.lite_llm.LiteLlm`.
- Produces:
  - `code_helper/__init__.py`: Exports `from . import agent`.
  - `code_helper/agent.py`: Exports `root_agent` (`coordinator` `LlmAgent`).
  - Coordinator routing behavior: Strictly routes questions to workers, never answers substantive code questions directly.

- [x] **Step 1: Write failing test verifying root_agent structure, sub-agents, and routing contract**

```python
# tests/test_coordinator.py
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
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_coordinator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'code_helper.agent'`

- [x] **Step 3: Implement `code_helper/__init__.py` and `code_helper/agent.py`**

- `code_helper/__init__.py`:
  ```python
  from . import agent
  __all__ = ["agent"]
  ```
- `code_helper/agent.py`:
  - Loads `.env` via `python-dotenv`.
  - Configures `LiteLlm(model="nvidia_nim/meta/llama-3.2-11b-vision-instruct")`.
  - Instantiates `code_searcher`, `code_explainer`, `architecture_mapper`, `onboarding_guide`.
  - Configures `root_agent = LlmAgent(name="coordinator", model=model, description="Routes developer questions to the appropriate specialized code worker.", instruction="You are the Boss Coordinator. You MUST NEVER answer substantive code questions yourself. Delegate strictly to: 'code_searcher' for finding specific snippets/terms, 'code_explainer' for explaining full files or functions, 'architecture_mapper' for dependencies/imports/call graphs, or 'onboarding_guide' for project setup and overview.", sub_agents=[searcher, explainer, mapper, guide])`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_coordinator.py -v`
Expected: PASS

---

### Task 5: Codebase Indexing Script (`index_codebase.py`) & Environment Scaffolding

**Files:**
- Create: `code_helper/index_codebase.py`
- Create: `.env.example`
- Create: `.gitignore`
- Test: `tests/test_indexing_script.py`

**Interfaces:**
- Consumes: Target repository (`.`), `.env` settings.
- Produces:
  - `code_helper/index_codebase.py`: Standalone CLI executable that reads repository files, chunks them, embeds them via NVIDIA NIM, and upserts them to Pinecone index `code-helper`.
  - Explicit exclusion rules: Ignores `code_helper/`, `tests/`, `.venv/`, `.git/`, `docs/`, `skills/`, `__pycache__/`, `*.json`.
  - Scans original Naive_RAG source files (`config.py`, `indexer.py`, `vector_store.py`, `query_pipeline.py`, `main.py`, `data/*.txt`).
  - CLI arguments: `--target-dir` (default `.`), `--chunk-size` (default 500), `--overlap` (default 50), `--dry-run`, `--evaluate`, `--clean`.
  - `.env.example`: Template for NVIDIA NIM and Pinecone credentials.
  - `.gitignore`: Ignores `.env`, `__pycache__`, virtualenvs, test caches, and local databases.

- [x] **Step 1: Write failing test for indexing script dry run and exclusion rules**

```python
# tests/test_indexing_script.py
from pathlib import Path
from code_helper.index_codebase import build_index, filter_indexable_files

def test_filter_indexable_files(tmp_path):
    (tmp_path / "main.py").write_text("# main", encoding="utf-8")
    (tmp_path / "config.py").write_text("# config", encoding="utf-8")
    helper_dir = tmp_path / "code_helper"
    helper_dir.mkdir()
    (helper_dir / "agent.py").write_text("# agent", encoding="utf-8")
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "lib.py").write_text("# lib", encoding="utf-8")

    files = filter_indexable_files(str(tmp_path))
    filenames = [Path(f).name for f in files]
    assert "main.py" in filenames
    assert "config.py" in filenames
    assert "agent.py" not in filenames  # Excludes code_helper implementation
    assert "lib.py" not in filenames    # Excludes .venv

def test_build_index_dry_run():
    # Dry run scans files and chunks without network calls
    result = build_index(target_dir=".", chunk_size=500, overlap=50, dry_run=True)
    assert result["files_scanned"] >= 5
    assert result["chunks_processed"] > 0
    assert result["dry_run"] is True
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_indexing_script.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'code_helper.index_codebase'`

- [x] **Step 3: Implement `index_codebase.py`, `.env.example`, and `.gitignore`**

- `code_helper/index_codebase.py`:
  - `filter_indexable_files(target_dir)`: Explicit exclusion of `code_helper`, `tests`, `.venv`, `.git`, `docs`, `skills`, `__pycache__`.
  - `build_index(target_dir=".", chunk_size=500, overlap=50, dry_run=False, evaluate=False, clean=False)`:
    - Calls `chunk_file()` on each indexable file.
    - If `dry_run=True`, prints chunk summary and returns statistics without making network calls.
    - If `evaluate=True`, runs chunk evaluation across specified chunk sizes.
    - If `dry_run=False`, initializes Pinecone, calls embedder (`input_type="passage"`), and batch upserts chunks to Pinecone index `code-helper`.
- `.env.example`:
  ```env
  NVIDIA_API_KEY=nvapi-your-key-here
  NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
  NVIDIA_CHAT_MODEL=meta/llama-3.2-11b-vision-instruct
  NVIDIA_EMBED_MODEL=nvidia/nemotron-3-embed-1b
  PINECONE_API_KEY=your-pinecone-api-key
  PINECONE_INDEX_NAME=code-helper
  PINECONE_CLOUD=aws
  PINECONE_REGION=us-east-1
  ```
- `.gitignore`: Ignores `.env`, `__pycache__`, `.pytest_cache`, `.venv`, `local_vector_db.json`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_indexing_script.py -v`
Expected: PASS

---

### Task 6: Verification, End-to-End Routing, Sample Q&A, and Complete README

**Files:**
- Create: `README.md`
- Create: `tests/test_end_to_end_routing.py`

**Interfaces:**
- Consumes: All 5 agents, repository codebase, custom RAG pipeline, MCP filesystem server.
- Produces:
  - `README.md` satisfying all Capstone Student Guide criteria:
    1. Helper summary (2-3 sentences explaining what this multi-agent assistant does).
    2. Table of Agents (Coordinator, Code Searcher, Code Explainer, Architecture Mapper, Onboarding Guide) with model, tools, and roles (highlighting Architecture Mapper as the non-AI agent).
    3. Table of Tools (listing all 7 plain Python tools + 1 custom RAG tool, separate from MCP tools).
    4. Chunk size evaluation comparing 200 vs 500 characters on this codebase with measured hit rates and clear rationale.
    5. MCP server documentation (Filesystem MCP configuration & usage).
    6. Exact setup and execution commands (`python code_helper/index_codebase.py`, `adk run code_helper`, `adk web`).
    7. 3 sample questions tested against this repo with answers and worker attribution.
    8. 1 problem encountered and how it was resolved (e.g., Windows path formatting for MCP / LiteLLM API key handling).
  - Integration test verifying end-to-end routing contract and README completeness.

- [x] **Step 1: Write failing test for README sections, routing contract, and fallback assertions**

```python
# tests/test_end_to_end_routing.py
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
    assert "MCP Server" in content
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
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_end_to_end_routing.py -v`
Expected: FAIL with `FileNotFoundError: README.md`

- [x] **Step 3: Create comprehensive README.md and verify all checklist items**

Write `README.md` containing all required tables, evaluation data, MCP documentation, run commands, 3 sample Q&As (Searcher, Explainer, Architecture Mapper), problem resolution, and verify all checklist items from the Student Guide.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_end_to_end_routing.py -v`
Expected: PASS

---

## Self-Review Checklist

1. **Spec coverage:**
   - 1 boss that only routes: Covered in Task 4.
   - 4 workers with clear descriptions: Covered in Task 3.
   - 8 custom tools (7 plain Python + 1 RAG search): Covered in Task 1 & Task 2.
   - Exactly 1 non-AI agent: `architecture_mapper` as `BaseAgent` in Task 3.
   - Custom RAG all 5 steps (no LangChain/LlamaIndex): Covered in Task 1.
   - Pinecone serverless index (dim 2048, cosine, `nvidia/nemotron-3-embed-1b`): Covered in Task 1 & Task 5.
   - Filesystem MCP on Code Explainer: Covered in Task 3.
   - Chunking evaluation with retrieval recall: Covered in Task 1, Task 5, & Task 6.
   - ADK folder layout & commands (`adk run code_helper`, `adk web`): Covered in Task 4 & Task 6.
   - 3 sample questions + 1 problem and fix: Covered in Task 6.
2. **Step scan:** Every step contains clear commands, explicit file paths, test code, and concrete assertions.
3. **Type consistency:** Consistent naming of `root_agent`, `code_helper`, tool functions, and worker agent names across all tasks.
4. **Review Focus:** Covered environment error handling, fallback responses (`"I could not find that"`), and Windows path handling.
5. **Proportion:** Clear, bite-sized tasks with explicit interfaces without bloat.
