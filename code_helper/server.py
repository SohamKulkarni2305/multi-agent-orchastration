"""
server.py — FastAPI REST Backend & Web Asset Server for Modern AI Agent Studio.
"""

import os
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from .agent import root_agent
    from .tools.diagram_tool import generate_architecture_diagram
    from .tools.health_check_tool import check_system_health, get_run_commands
except ImportError:
    from code_helper.agent import root_agent
    from code_helper.tools.diagram_tool import generate_architecture_diagram
    from code_helper.tools.health_check_tool import check_system_health, get_run_commands


class ChatRequest(BaseModel):
    message: str


AGENT_DISPLAY_NAMES = {
    "coordinator": "Boss Coordinator",
    "code_searcher": "Code Searcher",
    "architecture_mapper": "Architecture Mapper",
    "onboarding_guide": "Onboarding Guide",
    "code_explainer": "Code Explainer",
}

AGENT_ROSTER = [
    {
        "name": "coordinator",
        "title": "Boss Coordinator",
        "type": "Router (AI)",
        "badge": "Llama-3.2-11B",
        "color": "#818CF8",
        "description": "Orchestrates and delegates user queries strictly to specialized worker agents.",
    },
    {
        "name": "code_searcher",
        "title": "Code Searcher",
        "type": "Worker (AI)",
        "badge": "Pinecone RAG",
        "color": "#06B6D4",
        "description": "Locates functions, constants, and keywords using 5-step dense vector search and exact pattern matching.",
    },
    {
        "name": "architecture_mapper",
        "title": "Architecture Mapper",
        "type": "Worker (Deterministic)",
        "badge": "Static AST (0 AI)",
        "color": "#10B981",
        "description": "Maps module dependencies, symbol call sites, and Mermaid flowcharts with 100% mathematical precision.",
    },
    {
        "name": "onboarding_guide",
        "title": "Onboarding Guide",
        "type": "Worker (AI)",
        "badge": "Orientation",
        "color": "#F59E0B",
        "description": "Assists new developers with project structure, run commands, entrypoints, and environment health checks.",
    },
    {
        "name": "code_explainer",
        "title": "Code Explainer",
        "type": "Worker (AI)",
        "badge": "Filesystem MCP",
        "color": "#F43F5E",
        "description": "Reads source files live via Model Context Protocol and explains algorithms, design, and function logic.",
    },
]


def create_app(mock_mode: bool = False, static_dir: str = "web") -> FastAPI:
    """
    Factory function creating and configuring the FastAPI app for the Modern Agent Studio.
    """
    app = FastAPI(title="Multi-Agent Code Helper Studio", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_path = Path(static_dir).resolve()
    if not static_path.exists():
        # Fallback to root relative
        static_path = (Path(__file__).resolve().parent.parent / static_dir).resolve()

    @app.get("/api/status")
    async def get_status() -> dict[str, Any]:
        return {
            "status": "online",
            "app_name": "Multi-Agent Code Helper Studio",
            "model": "nvidia_nim/meta/llama-3.2-11b-vision-instruct",
            "embed_model": "nvidia/nemotron-3-embed-1b",
            "vector_db": "Pinecone Serverless (dim=2048, metric=cosine)",
            "index_name": os.getenv("PINECONE_INDEX_NAME", "code-helper"),
            "agents": AGENT_ROSTER,
        }

    @app.get("/api/diagram")
    async def get_diagram() -> dict[str, str]:
        diag = generate_architecture_diagram(".")
        # Strip outer markdown fences for raw Mermaid parsing if desired
        clean_mermaid = diag
        if "```mermaid" in diag:
            clean_mermaid = diag.split("```mermaid")[1].split("```")[0].strip()
        return {"mermaid": clean_mermaid, "raw_markdown": diag}

    @app.get("/api/health")
    async def get_health() -> dict[str, str]:
        report = check_system_health(".")
        return {"report": report}

    @app.get("/api/run-commands")
    async def get_commands() -> dict[str, str]:
        guide = get_run_commands()
        return {"guide": guide}

    @app.post("/api/chat")
    async def chat(request: ChatRequest) -> dict[str, Any]:
        query = request.message.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query message cannot be empty.")

        query_lower = query.lower()

        # Mock mode routing (used for offline tests or mock runs)
        if mock_mode:
            if any(w in query_lower for w in ["where", "chunk", "find", "search", "constant", "token"]):
                worker = "code_searcher"
                worker_type = "AI Agent (RAG)"
                tools_used = ["rag_search", "find_exact_matches"]
                ans = (
                    "Based on the indexed codebase in `indexer.py:L55-L111`, sliding window chunking "
                    "is implemented in `chunk_document()`. Window size: 500 chars, overlap: 50 chars."
                )
            elif any(w in query_lower for w in ["diagram", "mermaid", "flowchart", "import", "depend", "symbol", "call", "loc", "metric"]):
                worker = "architecture_mapper"
                worker_type = "Deterministic AST Engine (Zero AI)"
                tools_used = ["find_imports", "generate_architecture_diagram"]
                if "diagram" in query_lower or "flowchart" in query_lower:
                    ans = generate_architecture_diagram(".")
                else:
                    ans = (
                        "=== Module Dependencies ===\n"
                        "- `indexer.py` imports `config.py`\n"
                        "- `vector_store.py` imports `config.py`\n"
                        "- `query_pipeline.py` imports `config.py`, `vector_store.py`\n"
                        "- `main.py` imports `config.py`, `indexer.py`, `query_pipeline.py`\n"
                        "\n*Verified via static AST parsing with 0 LLM calls.*"
                    )
            elif any(w in query_lower for w in ["new", "start", "onboard", "setup", "run", "command"]):
                worker = "onboarding_guide"
                worker_type = "AI Agent (Guide)"
                tools_used = ["check_system_health", "get_run_commands"]
                ans = (
                    "Welcome to the Naive RAG project! Run `python -m code_helper.index_codebase --evaluate` "
                    "to index the codebase into Pinecone, then launch the agent with `adk run code_helper` or `python app.py`."
                )
            else:
                worker = "code_explainer"
                worker_type = "AI Agent (MCP)"
                tools_used = ["get_function_source", "read_file"]
                ans = (
                    "In `vector_store.py`, `VectorStore` initializes the Pinecone connection and handles "
                    "cosine similarity queries against the serverless 2048-dim index."
                )

            return {
                "worker": worker,
                "worker_name": AGENT_DISPLAY_NAMES.get(worker, worker),
                "worker_type": worker_type,
                "message": ans,
                "tools_used": tools_used,
            }

        # Real mode: Invoke ADK root_agent
        try:
            from google.adk.runners import InMemoryRunner
            from google.adk.events import Event

            runner = InMemoryRunner(agent=root_agent)
            
            # Run the agent asynchronously
            responding_worker = "coordinator"
            final_message = ""
            tools_called: list[str] = []

            async for event in runner.run_async(query):
                author = getattr(event, "author", "")
                if author and author != "user":
                    responding_worker = author
                if hasattr(event, "message") and event.message:
                    final_message = str(event.message)
                if hasattr(event, "tools") and event.tools:
                    tools_called.extend([str(t) for t in event.tools])

            if not final_message:
                final_message = "I have completed analyzing your request."

            worker_type = "Deterministic BaseAgent (0 AI)" if responding_worker == "architecture_mapper" else "AI Agent (LiteLLM)"

            return {
                "worker": responding_worker,
                "worker_name": AGENT_DISPLAY_NAMES.get(responding_worker, responding_worker),
                "worker_type": worker_type,
                "message": final_message,
                "tools_used": tools_called,
            }

        except Exception as e:
            # Fallback to deterministic handling on network error
            return {
                "worker": "coordinator",
                "worker_name": "Boss Coordinator",
                "worker_type": "Router (AI)",
                "message": f"Execution notice: {e}. Please check your NVIDIA and Pinecone credentials in .env.",
                "tools_used": [],
            }

    # Mount static assets if web directory exists
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

        @app.get("/")
        async def serve_index():
            index_file = static_path / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
            return {"message": "Modern AI Agent Studio backend is running. Create web/index.html to view UI."}

        @app.get("/{file_name:path}")
        async def serve_static_files(file_name: str):
            candidate = static_path / file_name
            if candidate.is_file():
                return FileResponse(str(candidate))
            index_file = static_path / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
            raise HTTPException(status_code=404, detail="File not found")

    return app
