# Design Specification: Modern AI Agent Studio Frontend

- **Date:** 2026-10-16
- **Topic:** Modern AI Agent Studio UI for Multi-Agent Code Helper
- **Author:** Pair Programming Agent
- **Target Repository:** Naive RAG Multi-Agent Code Helper

---

## 1. Executive Summary

The **Modern AI Agent Studio** is a glassmorphic web interface built to interact with and visualize the **Multi-Agent Code Helper** (composed of 1 Boss Coordinator and 4 specialized workers: Code Searcher, Architecture Mapper, Onboarding Guide, Code Explainer).

The interface provides real-time visualization of multi-agent routing decisions, live interactive Mermaid architecture diagrams, a chat console with worker attribution, and tool execution telemetry.

---

## 2. User Experience & Aesthetics

### 2.1 Theme & Design Tokens
- **Background:** Deep midnight slate (`#0B0F19`) with radial ambient gradients (`rgba(99, 102, 241, 0.08)` and `rgba(6, 182, 212, 0.06)`).
- **Surfaces:** Glassmorphic card panels (`background: rgba(17, 24, 39, 0.75)`, `backdrop-filter: blur(16px)`, `border: 1px solid rgba(255, 255, 255, 0.08)`, `box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35)`).
- **Typography:**
  - Headings: `Outfit`, sans-serif (weights 600, 700)
  - Body: `Inter`, sans-serif (weights 400, 500)
  - Code & Citations: `JetBrains Mono`, monospace
- **Agent Identity Color Palette:**
  - **Boss Coordinator:** Electric Violet (`#818CF8`, accent glow `rgba(129, 140, 248, 0.3)`)
  - **Code Searcher:** Neon Cyan (`#06B6D4`, accent glow `rgba(6, 182, 212, 0.3)`)
  - **Architecture Mapper:** Emerald Green (`#10B981`, accent glow `rgba(16, 185, 129, 0.3)`) — highlighted with `"100% Deterministic AST (0 AI)"` tag
  - **Onboarding Guide:** Warm Amber (`#F59E0B`, accent glow `rgba(245, 158, 11, 0.3)`)
  - **Code Explainer:** Radiant Rose (`#F43F5E`, accent glow `rgba(244, 63, 94, 0.3)`) — highlighted with `"Filesystem MCP"` tag

---

## 3. Layout & Interactive Components

The layout is arranged as a two-column responsive desktop studio:

### 3.1 Studio Header
- Project Title (`Multi-Agent Code Helper Studio`) with status badge (`Online • 5 Agents Active`).
- Live system status pills:
  - `NVIDIA NIM`: `Connected (Llama-3.2-11b + Nemotron-1B)`
  - `Pinecone`: `code-helper (2048-dim cosine)`
  - `MCP Server`: `@modelcontextprotocol/server-filesystem`
- Quick Action buttons:
  - `System Health`: Triggers system diagnostic
  - `Reset Session`: Clears current conversation history

### 3.2 Left Column: Visual Orchestration & Architecture Stage
1. **Interactive Multi-Agent Routing Map:**
   - Visual hierarchy showing Boss Coordinator at the top, branching downward to the 4 worker nodes via an HTML5 Canvas / SVG line network.
   - When a user submits a query:
     - An animated pulse travel along the connector line from Boss to the target worker.
     - The target worker card glows and pulses with an active status badge while executing tools.
     - Inactive worker cards remain dimmed with subtle border styling.
2. **Live Architecture Mermaid Diagram Viewer:**
   - Ingests the dynamic output of `generate_architecture_diagram()`.
   - Embedded Mermaid.js renders the live flowchart (`graph TD`) mapping `main.py` -> `config.py`, `indexer.py`, `vector_store.py`, `query_pipeline.py`.
   - Controls: Zoom In, Zoom Out, Reset, Re-fetch Diagram.

### 3.3 Right Column: Interactive Chat & Tool Telemetry Console
1. **Conversation Stream:**
   - User messages displayed in styled bubble cards.
   - Agent responses formatted in GitHub Flavored Markdown (headings, code blocks, lists).
   - Prominent **Worker Attribution Badge** on each response:
     - E.g. `[Code Searcher] • Pinecone Vector RAG`
     - E.g. `[Architecture Mapper] • Static AST Engine (Zero AI)`
     - E.g. `[Code Explainer] • Filesystem MCP`
     - E.g. `[Onboarding Guide] • Project Orientation`
2. **Tool Execution Telemetry Drawer:**
   - Expandable disclosure below each agent response showing the exact tool invoked, execution time, and citation metadata (e.g. `config.py:L70-L105`).
3. **Quick-Action Prompt Pills:**
   - `Where is chunking defined?` (Code Searcher test)
   - `Explain vector_store.py` (Code Explainer test)
   - `Which files import config.py?` (Architecture Mapper test)
   - `I am new, where do I start?` (Onboarding Guide test)
   - `Generate system architecture diagram` (Diagram Generator test)
4. **Docked Prompt Input:**
   - Auto-expanding textarea.
   - Submit button with spinner during execution.
   - Keyboard listener (`Enter` to submit, `Shift+Enter` for line break).

---

## 4. Technical Architecture & Endpoints

### 4.1 Server Module (`code_helper/server.py` & `app.py`)
- Python web application powered by `FastAPI` and `uvicorn`.
- Mounts static files from `web/`.
- Endpoints:
  - `GET /`: Serves `web/index.html`.
  - `GET /api/status`: Returns agent team roster, model configurations, and Pinecone index status.
  - `POST /api/chat`:
    - Payload: `{ "message": str }`
    - Logic: Invokes the multi-agent system (`code_helper.agent.root_agent`). Detects the responding worker and active tool calls from the invocation events.
    - Response:
      ```json
      {
        "worker": "code_searcher",
        "worker_name": "Code Searcher",
        "worker_type": "AI Agent",
        "message": "...",
        "tools_used": ["rag_search"],
        "timestamp": "2026-10-16T02:40:00"
      }
      ```
  - `GET /api/diagram`: Calls `generate_architecture_diagram(".")` and returns raw Mermaid code string.
  - `GET /api/health`: Calls `check_system_health(".")`.
  - `GET /api/run-commands`: Calls `get_run_commands()`.

### 4.2 Single Command Entrypoint (`app.py`)
- Running `python app.py`:
  1. Checks `.env` configuration.
  2. Launches Uvicorn server on `http://127.0.0.1:8000`.
  3. Automatically opens the user's default browser to `http://127.0.0.1:8000`.

---

## 5. Directory Layout

```
capstone_project/
├── app.py                          # Single-command launcher for Modern AI Agent Studio
├── code_helper/
│   ├── server.py                   # FastAPI backend server with REST endpoints
│   ├── agent.py                    # Multi-agent root coordinator
│   ├── agents/                     # Worker agents
│   ├── rag/                        # 5-step RAG pipeline
│   └── tools/                      # 13 deterministic and RAG tools
└── web/                            # Frontend static web application
    ├── index.html                  # Semantic HTML5 layout
    ├── style.css                   # Modern CSS design system (glassmorphism, animations)
    └── app.js                      # UI logic, routing map canvas, Mermaid renderer
```

---

## 6. Self-Review & Verification

1. **Placeholder scan:** No TBDs, TODOs, or mock placeholders. All endpoints map directly to existing python functions.
2. **Internal consistency:** Agent names, models, and tool mappings align exactly with `code_helper/agent.py` and the Student Guide PDF.
3. **Scope check:** Focused purely on creating the visual studio dashboard and server wrapper for existing verified agents.
4. **Resilience:** Graceful error handling for offline testing, network timeouts, and browser compatibility.
