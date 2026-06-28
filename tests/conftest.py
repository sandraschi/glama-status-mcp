import tempfile
from pathlib import Path

import pytest

from glama_status_mcp.config import DATA_DIR


@pytest.fixture(autouse=True)
def temp_data_dir(monkeypatch, tmp_path: Path):
    """Redirect DATA_DIR to a temp directory for test isolation."""
    import importlib

    monkeypatch.setattr(
        "glama_status_mcp.config.DATA_DIR", tmp_path
    )
    monkeypatch.setattr(
        "glama_status_mcp.config.DB_PATH", tmp_path / "test_glama_status.db"
    )
    # Reload database module to pick up new DB_PATH
    import glama_status_mcp.database as dbmod
    importlib.reload(dbmod)
    yield tmp_path
    # Cleanup
    db = tmp_path / "test_glama_status.db"
    if db.exists():
        db.unlink()


@pytest.fixture
def sample_html_steam() -> str:
    """Minimal HTML snippet matching Glama score page structure."""
    return """<html><body>
<span class="kIIaya">A</span>
<span class="czikZZ">5.0 / 5</span>
<button class="ULqjq"><a href="/tools/steam_game_info">steam_game_info</a></button>
<div><span class="czikZZ">4.2 / 5</span></div>
</body></html>"""


@pytest.fixture
def fleet_repos():
    from glama_status_mcp.models import FleetRepo
    return [
        FleetRepo(name="test-mcp", glama_author="sandraschi"),
        FleetRepo(name="other-mcp", glama_author="sandraschi"),
    ]


@pytest.fixture
def sample_repo_score():
    from glama_status_mcp.models import RepoScore, ToolScore, ServerCoherence
    return RepoScore(
        name="test-mcp",
        overall_grade="A",
        overall_score=4.0,
        tdqs_grade="A",
        tdqs_mean=4.2,
        tdqs_min=3.8,
        coherence=ServerCoherence(grade="A"),
        maintenance_grade="A",
        tools=[
            ToolScore(name="test_tool_1", grade="A", score=4.5),
            ToolScore(name="test_tool_2", grade="B", score=3.5),
        ],
    )
