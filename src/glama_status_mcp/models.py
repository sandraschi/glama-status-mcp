"""Pydantic models + fleet repo list.

FLEET_REPOS is the default tracked list. To track repos from
any Glama author, add entries via glama_status(operation="add_repo")
or edit the `config/fleet-repos.json` file in the repo root.
"""

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = REPO_ROOT / "config" / "fleet-repos.json"
DEFAULT_AUTHOR = os.environ.get("GLAMA_AUTHOR", "sandraschi")


class ToolScore(BaseModel):
    name: str
    grade: str
    score: float
    purpose: float = 0.0
    usage_guidelines: float = 0.0
    behavior: float = 0.0
    parameters: float = 0.0
    conciseness: float = 0.0
    completeness: float = 0.0


class ServerCoherence(BaseModel):
    grade: str = ""
    disambiguation: float = 0.0
    naming_consistency: float = 0.0
    tool_count: float = 0.0
    completeness: float = 0.0


class RepoScore(BaseModel):
    name: str
    glama_namespace: str = "sandraschi"
    glama_slug: str = ""
    overall_grade: str = ""
    overall_score: float = 0.0
    profile_completion: int = 0
    coherence: ServerCoherence = Field(default_factory=ServerCoherence)
    tdqs_grade: str = ""
    tdqs_mean: float = 0.0
    tdqs_min: float = 0.0
    maintenance_grade: str = ""
    tools: list[ToolScore] = Field(default_factory=list)
    last_scraped: str = ""
    latest_release: str = ""


class FleetRepo(BaseModel):
    name: str
    glama_author: str = "sandraschi"
    glama_slug: str = ""
    active: bool = True

    def score_url(self) -> str:
        slug = self.glama_slug or self.name
        return f"https://glama.ai/mcp/servers/{self.glama_author}/{slug}/score"


def _default_fleet() -> list[FleetRepo]:
    """Default demo fleet -- example MCP servers with Glama scores."""
    return [
        FleetRepo(name="virtualization-mcp"),
        FleetRepo(name="bumi-mcp"),
        FleetRepo(name="blender-mcp"),
        FleetRepo(name="windows-operations-mcp"),
        FleetRepo(name="worldlabs-mcp"),
        FleetRepo(name="robotics-mcp"),
        FleetRepo(name="xkcd-mcp"),
        FleetRepo(name="cursor-mcp"),
        FleetRepo(name="steam-mcp"),
        FleetRepo(name="email-mcp"),
    ]


def load_fleet_repos() -> list[FleetRepo]:
    """Load fleet repos from config file, falling back to defaults."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            repos = []
            for entry in data:
                repos.append(FleetRepo(
                    name=entry["name"],
                    glama_author=entry.get("glama_author", DEFAULT_AUTHOR),
                    glama_slug=entry.get("glama_slug", ""),
                    active=entry.get("active", True),
                ))
            if repos:
                return repos
        except (json.JSONDecodeError, KeyError):
            pass

    # Write default config if missing
    _save_fleet(_default_fleet())
    return _default_fleet()


def _save_fleet(repos: list[FleetRepo]) -> None:
    """Persist fleet repo list to config file."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = []
    for r in repos:
        data.append({
            "name": r.name,
            "glama_author": r.glama_author,
            "glama_slug": r.glama_slug,
            "active": r.active,
        })
    CONFIG_FILE.write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def add_repo(name: str, author: str = "", slug: str = "") -> FleetRepo:
    """Add a repo to the fleet and persist."""
    repos = load_fleet_repos()
    existing = [r for r in repos if r.name == name]
    if existing:
        return existing[0]
    new = FleetRepo(
        name=name,
        glama_author=author or DEFAULT_AUTHOR,
        glama_slug=slug,
    )
    repos.append(new)
    _save_fleet(repos)
    return new


def remove_repo(name: str) -> bool:
    """Remove a repo from the fleet config. Returns True if removed."""
    repos = load_fleet_repos()
    filtered = [r for r in repos if r.name != name]
    if len(filtered) == len(repos):
        return False
    _save_fleet(filtered)
    return True


FLEET_REPOS: list[FleetRepo] = load_fleet_repos()
