# Modern AI Agent Studio Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a glassmorphic web interface ("Modern AI Agent Studio") for the Multi-Agent Code Helper featuring an interactive multi-agent routing map, live dynamic Mermaid architecture diagram viewer, real-time chat console with worker attribution, and single-command launcher (`python app.py`).

**Architecture:** A lightweight FastAPI/Starlette backend (`code_helper/server.py` and `app.py`) exposing REST endpoints that invoke `code_helper.agent.root_agent` and existing deterministic tools, serving a vanilla HTML5/CSS3/JS single-page application in `web/` with GPU-accelerated CSS animations and embedded Mermaid.js.

**Tech Stack:** Python 3.10+, `fastapi`, `uvicorn`, `google-adk`, HTML5 Canvas / SVG, Vanilla CSS (Glassmorphism, CSS Custom Properties), Vanilla JavaScript (ES6+), Mermaid.js (via CDN).

**Spec:** `docs/superpowers/specs/2026-10-16-modern-agent-studio-ui-design.md`

## Global Constraints

- Backend must use FastAPI and Uvicorn already available in the Python environment (as part of Google ADK dependencies).
- Frontend must not require Node.js, npm, or build bundlers (pure HTML5, Vanilla CSS, and modern ES6 JS).
- Dark-mode aesthetic: deep midnight slate (`#0B0F19`), surface cards (`rgba(17, 24, 39, 0.75)` with `backdrop-filter: blur(16px)`), and neon agent color badges.
- Worker identity colors: Boss Coordinator (`#818CF8`), Code Searcher (`#06B6D4`), Architecture Mapper (`#10B981`), Onboarding Guide (`#F59E0B`), Code Explainer (`#F43F5E`).
- Must run cleanly cross-platform on Windows using forward-slash path resolution.
- All new tests must pass offline without live network credential requirements.

## Review Focus

1. **Async agent execution without event loop collisions:** In `code_helper/server.py`, invoking `root_agent._run_async_impl` or ADK runner within an existing FastAPI async event loop must await generator events cleanly without `RuntimeError: This event loop is already running`.
2. **Worker attribution accuracy:** When `root_agent` delegates to a worker, the server must inspect invocation events to accurately identify the specific worker agent that answered (e.g. `code_searcher`, `architecture_mapper`, `code_explainer`, `onboarding_guide`) rather than attributing to coordinator.
3. **Mermaid rendering resilience:** If raw Mermaid syntax contains markdown code fences (```mermaid ... ```), `web/app.js` must strip fence markers and sanitize labels before passing to `mermaid.render()` to avoid SVG parse syntax errors.
4. **Canvas high-DPI scaling:** The interactive routing map on HTML5 Canvas must account for `window.devicePixelRatio` so connector lines and pulses remain crisp on high-DPI/Retina screens.
5. **Static file serving and graceful fallback:** If `web/` directory is accessed directly or through reverse proxy, root `/` must serve `web/index.html` with correct MIME types for CSS and JS.

---

### Task 1: Backend Server Module & REST API (`code_helper/server.py`)

**Files:**
- Create: `code_helper/server.py`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes:
  - `code_helper.agent.root_agent`
  - `code_helper.tools.diagram_tool.generate_architecture_diagram`
  - `code_helper.tools.health_check_tool.check_system_health`
  - `code_helper.tools.health_check_tool.get_run_commands`
- Produces:
  - `create_app() -> FastAPI`: Configures FastAPI application, mounts `web/` static files at `/`, and registers REST endpoints:
    - `GET /api/status -> dict`: Status of agents, models, and Pinecone index.
    - `POST /api/chat -> dict`: Invokes agent with `{ "message": str }` and returns `{ "worker": str, "worker_name": str, "worker_type": str, "message": str, "tools_used": list[str] }`.
    - `GET /api/diagram -> dict`: Returns `{ "mermaid": str }` containing clean Mermaid syntax.
    - `GET /api/health -> dict`: Returns `{ "report": str }`.
    - `GET /api/run-commands -> dict`: Returns `{ "guide": str }`.

- [ ] **Step 1: Write failing test for server endpoints**

```python
# tests/test_server.py
import pytest
from fastapi.testclient import TestClient
from code_helper.server import create_app

@pytest.fixture
def client():
    app = create_app(mock_mode=True)
    return TestClient(app)

def test_api_status_endpoint(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "agents" in data
    assert len(data["agents"]) == 5

def test_api_diagram_endpoint(client):
    res = client.get("/api/diagram")
    assert res.status_code == 200
    data = res.json()
    assert "mermaid" in data
    assert "graph TD" in data["mermaid"]

def test_api_chat_endpoint(client):
    res = client.post("/api/chat", json={"message": "Where is chunking defined?"})
    assert res.status_code == 200
    data = res.json()
    assert "worker" in data
    assert "message" in data
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_server.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'code_helper.server'`

- [ ] **Step 3: Implement `code_helper/server.py`**

Create FastAPI app with static file mounting and endpoints. For `/api/chat`:
- When `mock_mode=True` (used during offline tests): deterministic mock dispatcher based on query keywords.
- When `mock_mode=False`: run `root_agent` using ADK's `InvocationContext` and capture the responding worker name from the yielded `Event` metadata.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_server.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add code_helper/server.py tests/test_server.py
git commit -m "feat(server): add FastAPI backend and REST endpoints for UI"
```

---

### Task 2: Single-Command Entrypoint (`app.py`)

**Files:**
- Create: `app.py`
- Test: `tests/test_app_entrypoint.py`

**Interfaces:**
- Consumes: `code_helper.server.create_app`
- Produces: CLI script with arguments:
  - `--port` (default: 8000)
  - `--host` (default: "127.0.0.1")
  - `--no-browser` (flag to suppress automatic browser launch)

- [ ] **Step 1: Write failing test for app launcher configuration**

```python
# tests/test_app_entrypoint.py
import pytest
from app import build_parser

def test_app_argument_parser():
    parser = build_parser()
    args = parser.parse_args(["--port", "9000", "--no-browser"])
    assert args.port == 9000
    assert args.no_browser is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_app_entrypoint.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Implement `app.py`**

Implement `build_parser()`, `main()`, and browser opener (`webbrowser.open(f"http://{host}:{port}")` in a delayed daemon thread).

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_app_entrypoint.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app_entrypoint.py
git commit -m "feat(app): add single-command launcher script with auto browser opening"
```

---

### Task 3: Modern Studio Design System & Layout (`web/index.html` & `web/style.css`)

**Files:**
- Create: `web/index.html`
- Create: `web/style.css`

**Interfaces:**
- Consumes: Google Fonts (`Outfit`, `Inter`, `JetBrains Mono`), FontAwesome / Lucide icons CDN, Mermaid.js CDN (`https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js`).
- Produces:
  - Responsive two-column studio layout.
  - CSS custom properties (`--bg-primary: #0B0F19`, `--card-bg: rgba(17, 24, 39, 0.75)`, etc.).
  - Glassmorphic card utility classes, neon glow states, and pulse animation keyframes.

- [ ] **Step 1: Create `web/index.html` structure**

Include:
- Top bar with studio brand, system health indicator, Pinecone/NVIDIA status badges.
- Left column (Visual Stage):
  - Card 1: **Multi-Agent Routing Canvas** with container for Boss and 4 worker nodes.
  - Card 2: **Live Architecture Diagram Viewer** with Mermaid SVG viewport and zoom/reset toolbar.
- Right column (Interactive Console):
  - Agent conversation stream with worker attribution headers.
  - Quick-action prompt chips.
  - Auto-expanding input dock with send button.

- [ ] **Step 2: Create `web/style.css` design system**

Implement complete design tokens:
- Modern CSS grid layout (`display: grid; grid-template-columns: 1.15fr 1fr`).
- Glassmorphic backdrop filter blur (`backdrop-filter: blur(16px)`).
- Agent accent borders and glowing shadows for active states.
- Clean typography and custom scrollbars.
- Keyframe animations: `@keyframes pulse-glow`, `@keyframes flow-pulse`, `@keyframes fade-in`.

- [ ] **Step 3: Commit**

```bash
git add web/index.html web/style.css
git commit -m "feat(ui): implement modern studio layout and glassmorphism design system"
```

---

### Task 4: Interactive Client Application Logic (`web/app.js`)

**Files:**
- Create: `web/app.js`

**Interfaces:**
- Consumes:
  - `GET /api/status`
  - `POST /api/chat`
  - `GET /api/diagram`
  - `GET /api/health`
  - Global `mermaid` library
- Produces:
  - Live Canvas Particle Routing Engine: draws smooth Bézier curves from Boss Coordinator to the 4 worker cards. When a message is sent, triggers glowing particle pulses toward the active worker.
  - Mermaid Diagram Engine: fetches raw Mermaid code from `/api/diagram`, sanitizes it, and renders crisp SVG inside the diagram container.
  - Chat Controller: handles user inputs, streaming display, quick-question pills, markdown rendering, and collapsible tool telemetry blocks.

- [ ] **Step 1: Implement routing canvas visualizer**

Create `RoutingVisualizer` class:
- Calculates coordinates of Boss Coordinator card and the 4 Worker cards (`code_searcher`, `code_explainer`, `architecture_mapper`, `onboarding_guide`).
- Renders glowing connector lines on HTML5 Canvas.
- Triggers particle pulse animation toward the selected worker during query processing.

- [ ] **Step 2: Implement live Mermaid diagram viewer**

Create `DiagramViewer` class:
- Initializes Mermaid with dark theme (`theme: 'dark', themeVariables: { darkMode: true, background: '#0B0F19' }`).
- Fetches `/api/diagram` on load and renders into `#diagram-container`.
- Implements zoom in, zoom out, and reset transforms.

- [ ] **Step 3: Implement Chat & Tool Telemetry Controller**

Create `ChatController` class:
- Sends user prompt to `/api/chat`.
- Updates routing visualizer to highlight the active worker with pulse animation.
- Renders response card with Worker Attribution tag, formatted code snippets, and expandable tool execution telemetry.
- Binds quick-question chips to auto-submit queries.

- [ ] **Step 4: Commit**

```bash
git add web/app.js
git commit -m "feat(ui): implement interactive routing canvas, mermaid rendering, and chat controller"
```

---

### Task 5: End-to-End Integration, Browser Verification & Documentation Update

**Files:**
- Modify: `README.md`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: All components from Tasks 1-4.
- Produces:
  - Verification that `python app.py --no-browser` boots and responds with 200 OK across all endpoints and serves static assets.
  - Updated `README.md` documenting the Modern AI Agent Studio launcher and features.

- [ ] **Step 1: Add full integration test in `tests/test_server.py`**

```python
def test_static_assets_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Multi-Agent Code Helper" in res.text
    assert "app.js" in res.text

    css_res = client.get("/style.css")
    assert css_res.status_code == 200
    assert "--bg-primary" in css_res.text

    js_res = client.get("/app.js")
    assert js_res.status_code == 200
```

- [ ] **Step 2: Run pytest to verify all unit & integration tests pass**

Run: `pytest -v`
Expected: All tests pass.

- [ ] **Step 3: Update `README.md` with Modern Studio UI instructions**

Add section detailing:
- Single-command studio launch: `python app.py`
- Features: Live Multi-Agent Routing Canvas, Dynamic Mermaid Architecture Viewer, Quick-Action Question Pills, Tool Execution Telemetry.

- [ ] **Step 4: Final commit**

```bash
git add README.md tests/test_server.py
git commit -m "docs: update README with Modern AI Agent Studio UI documentation"
```
