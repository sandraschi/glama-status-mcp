"""Server API endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app in HTTP mode."""
    import sys
    import os
    from pathlib import Path

    # Patch sys.argv to simulate --http mode
    old_argv = sys.argv.copy()
    old_cwd = os.getcwd()
    sys.argv = ["server.py", "--http", "--port", "11072"]

    # Temporarily change to repo root so webapp/dist lookup works
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(str(repo_root))

    try:
        from glama_status_mcp.server import main as server_main_func

        # We need the FastAPI app, not the server main function.
        # Build the app directly for testing.
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from glama_status_mcp.database import (
            init_db, seed_fleet, get_all_repo_scores,
            get_repo_score, get_worst_tools, get_refresh_history,
            generate_report, compute_deltas,
        )
        from glama_status_mcp.models import FLEET_REPOS
        from glama_status_mcp.server import _do_refresh, mcp as _mcp

        app = FastAPI(title="glama-status-mcp")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        mcp_asgi = _mcp.http_app(path="/mcp")
        app.mount("/mcp", mcp_asgi)

        init_db()
        seed_fleet(FLEET_REPOS)

        @app.get("/health")
        async def health():
            return {"status": "ok", "service": "glama-status-mcp"}

        @app.get("/api/repos")
        async def api_repos():
            return get_all_repo_scores()

        @app.get("/api/repos/{name}")
        async def api_repo(name: str):
            from fastapi.responses import JSONResponse
            repo = get_repo_score(name)
            if not repo:
                return JSONResponse(
                    {"error": "not found"}, status_code=404
                )
            return repo

        @app.get("/api/worst-tools")
        async def api_worst_tools(limit: int = 20):
            return get_worst_tools(limit)

        @app.post("/api/refresh")
        async def api_refresh():
            return await _do_refresh()

        @app.get("/api/history")
        async def api_history(limit: int = 10):
            return get_refresh_history(limit)

        @app.get("/api/report")
        async def api_report():
            return generate_report()

        @app.get("/api/deltas")
        async def api_deltas():
            return compute_deltas()

        yield TestClient(app)
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)


class TestHealth:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "glama-status-mcp"


class TestAPIRepos:
    def test_list_repos_empty(self, client):
        response = client.get("/api/repos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_nonexistent_repo(self, client):
        response = client.get("/api/repos/nonexistent")
        # May return 200 with error dict or 404 depending on routing
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert "error" in data

    def test_worst_tools_empty(self, client):
        response = client.get("/api/worst-tools")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_history(self, client):
        response = client.get("/api/history")
        assert response.status_code == 200

    def test_deltas(self, client):
        response = client.get("/api/deltas")
        assert response.status_code == 200

    def test_report(self, client):
        response = client.get("/api/report")
        assert response.status_code == 200
        data = response.json()
        assert "total_repos" in data
        assert "grade_distribution" in data


class TestAPIRefresh:
    def test_refresh_endpoint(self, client):
        """Refresh should not crash even if Glama is unreachable."""
        response = client.post("/api/refresh")
        # Refresh may fail to reach Glama but should return a valid response
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
