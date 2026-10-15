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

