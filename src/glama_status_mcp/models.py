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
    glama_slug: str = ""
    active: bool = True

    def score_url(self) -> str:
        slug = self.glama_slug or self.name
        return f"https://glama.ai/mcp/servers/{self.glama_author}/{slug}/score"


# All 35 sandraschi repos found on Glama via API
# slug overrides for repos where Glama slug differs from repo name
FLEET_REPOS: list[FleetRepo] = [
    FleetRepo(name="virtualization-mcp"),
    FleetRepo(name="bumi-mcp"),
    FleetRepo(name="freecad-mcp"),
    FleetRepo(name="database-operations-mcp"),
    FleetRepo(name="filesystem-mcp"),
    FleetRepo(name="windows-computer-use-mcp", glama_slug="windows-computer-use-mcp"),
    FleetRepo(name="ittybittyvideos", glama_slug="ittybittyvideos"),
    FleetRepo(name="calibre-mcp", glama_slug="calibremcp"),
    FleetRepo(name="plex-mcp", glama_slug="plexmcp"),
    FleetRepo(name="nest-protect-mcp"),
    FleetRepo(name="logic-analyzer-mcp"),
    FleetRepo(name="oscilloscope-mcp"),
    FleetRepo(name="cursor-mcp"),
    FleetRepo(name="xkcd-mcp"),
    FleetRepo(name="openbci-mcp"),
    FleetRepo(name="worldlabs-mcp"),
    FleetRepo(name="blender-mcp"),
    FleetRepo(name="openclaude-mcp"),
    FleetRepo(name="ai-producer-hub"),
    FleetRepo(name="inkscape-mcp"),
    FleetRepo(name="steam-mcp"),
    FleetRepo(name="nuki-mcp"),
    FleetRepo(name="streamfog-mcp"),
    FleetRepo(name="sdr-mcp"),
    FleetRepo(name="opencode-cli-mcp"),
    FleetRepo(name="email-mcp"),
    FleetRepo(name="discord-mcp"),
    FleetRepo(name="openclaw-molt-mcp"),
    FleetRepo(name="directmedia-mcp"),
    FleetRepo(name="observability-mcp"),
    FleetRepo(name="ocr-mcp"),
    FleetRepo(name="robotics-mcp"),
    FleetRepo(name="tailscale-mcp"),
    FleetRepo(name="notepadpp-mcp"),
    FleetRepo(name="windows-operations-mcp"),
]
