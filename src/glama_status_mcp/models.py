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


# 10 sandraschi repos with actual Glama scores (out of 35 registered)
# slug overrides for repos where Glama slug differs from repo name
FLEET_REPOS: list[FleetRepo] = [
    FleetRepo(name="virtualization-mcp"),               # B   3.06  9 tools
    FleetRepo(name="bumi-mcp"),                         # A   3.64  2 tools
    FleetRepo(name="blender-mcp"),                      # C   2.70  67 tools
    FleetRepo(name="windows-operations-mcp"),           # B   3.00  17 tools
    FleetRepo(name="worldlabs-mcp"),                    # B   3.38  20 tools
    FleetRepo(name="robotics-mcp"),                     # A   3.58  8 tools
    FleetRepo(name="xkcd-mcp"),                         # A   3.67  6 tools
    FleetRepo(name="cursor-mcp"),                       # A   3.80  6 tools
    FleetRepo(name="steam-mcp"),                        # A   3.81  14 tools
    FleetRepo(name="email-mcp"),                        # A   3.82  10 tools
]
