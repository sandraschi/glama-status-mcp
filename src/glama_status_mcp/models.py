from datetime import datetime
from pydantic import BaseModel, Field


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
    active: bool = True


FLEET_REPOS: list[FleetRepo] = [
    FleetRepo(name="virtualization-mcp"),
    FleetRepo(name="bumi-mcp"),
    FleetRepo(name="leanforge-mcp"),
    FleetRepo(name="freecad-mcp"),
    FleetRepo(name="qcad-mcp"),
    FleetRepo(name="arxiv-mcp"),
    FleetRepo(name="aiwatcher-mcp"),
    FleetRepo(name="yahboom-mcp"),
    FleetRepo(name="devices-mcp"),
    FleetRepo(name="plex-mcp"),
    FleetRepo(name="calibre-mcp"),
    FleetRepo(name="robotics-mcp"),
    FleetRepo(name="godot-mcp"),
    FleetRepo(name="system-admin-mcp"),
    FleetRepo(name="database-operations-mcp"),
    FleetRepo(name="worldlabs-mcp"),
    FleetRepo(name="blender-mcp"),
    FleetRepo(name="gimp-mcp"),
    FleetRepo(name="inkscape-mcp"),
    FleetRepo(name="unity3d-mcp"),
    FleetRepo(name="git-github-mcp"),
    FleetRepo(name="docker-mcp"),
]
