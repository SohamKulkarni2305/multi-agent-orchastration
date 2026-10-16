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
    agent_names = [a["name"] for a in data["agents"]]
    assert "coordinator" in agent_names
    assert "code_searcher" in agent_names
    assert "architecture_mapper" in agent_names


def test_api_diagram_endpoint(client):
    res = client.get("/api/diagram")
    assert res.status_code == 200
    data = res.json()
    assert "mermaid" in data
    assert "graph TD" in data["mermaid"]


def test_api_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "report" in data
    assert "Health" in data["report"] or "Python" in data["report"]


def test_api_run_commands_endpoint(client):
    res = client.get("/api/run-commands")
    assert res.status_code == 200
    data = res.json()
    assert "guide" in data
    assert "code_helper" in data["guide"]


def test_api_chat_endpoint(client):
    res = client.post("/api/chat", json={"message": "Where is chunking defined?"})
    assert res.status_code == 200
    data = res.json()
    assert "worker" in data
    assert "worker_name" in data
    assert "message" in data
    assert data["worker"] == "code_searcher"


def test_static_assets_served(client):
    # Test index.html served at root
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "Multi-Agent Code Helper" in res_root.text
    assert "routing-canvas" in res_root.text

    # Test CSS served
    res_css = client.get("/style.css")
    assert res_css.status_code == 200
    assert "--bg-primary" in res_css.text

    # Test JS served
    res_js = client.get("/app.js")
    assert res_js.status_code == 200
    assert "RoutingVisualizer" in res_js.text


def test_api_codebase_endpoint(client):
    res = client.get("/api/codebase")
    assert res.status_code == 200
    data = res.json()
    assert "name" in data
    assert "files_count" in data
    assert "files" in data


def test_api_upload_code_and_reset(client):
    # Test uploading Python files via JSON endpoint
    payload = {
        "filename": "Uploaded Files",
        "files": {
            "calculator.py": "def add(a, b):\n    return a + b\n\ndef multiply(a, b):\n    return a * b\n"
        }
    }
    res_upload = client.post("/api/upload-code", json=payload)
    assert res_upload.status_code == 200
    data_upload = res_upload.json()
    assert data_upload["status"] == "success"
    assert "calculator.py" in str(data_upload["info"]["files"])

    # Test diagram endpoint reflects uploaded codebase
    res_diag = client.get("/api/diagram")
    assert res_diag.status_code == 200
    assert "calculator.py" in res_diag.json()["mermaid"]

    # Test chat endpoint answers about uploaded code
    res_chat = client.post("/api/chat", json={"message": "Where is add defined?"})
    assert res_chat.status_code == 200
    assert "calculator.py" in res_chat.json()["message"]

    # Reset back to default workspace
    res_reset = client.post("/api/reset-codebase")
    assert res_reset.status_code == 200
    assert res_reset.json()["status"] == "success"


def test_api_file_specific_diagram_endpoint(client):
    res = client.get("/api/diagram?file=indexer.py")
    assert res.status_code == 200
    data = res.json()
    assert data["target_file"] == "indexer.py"
    assert data["is_file_diagram"] is True
    assert "indexer.py" in data["mermaid"]
    assert "load_document" in data["mermaid"]
    assert "run_indexing_pipeline" in data["mermaid"]


def test_api_chat_file_diagram_intent(client):
    res = client.post("/api/chat", json={"message": "Generate architecture diagram for indexer.py"})
    assert res.status_code == 200
    data = res.json()
    assert data["worker"] == "architecture_mapper"
    assert data["target_file"] == "indexer.py"
    assert "mermaid" in data
    assert "indexer.py" in data["mermaid"]



