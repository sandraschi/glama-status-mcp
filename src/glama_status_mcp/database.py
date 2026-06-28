import json
import sqlite3
from datetime import UTC, datetime

from glama_status_mcp.config import DB_PATH
from glama_status_mcp.models import FleetRepo, RepoScore


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS repos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            glama_namespace TEXT NOT NULL DEFAULT 'sandraschi',
            glama_slug TEXT,
            overall_grade TEXT,
            overall_score REAL,
            coherence_grade TEXT,
            coherence_disambiguation REAL DEFAULT 0,
            coherence_naming REAL DEFAULT 0,
            coherence_tool_count REAL DEFAULT 0,
            coherence_completeness REAL DEFAULT 0,
            tdqs_grade TEXT,
            tdqs_mean REAL,
            tdqs_min REAL,
            maintenance_grade TEXT,
            profile_completion INTEGER DEFAULT 0,
            latest_release TEXT,
            last_scraped TIMESTAMP,
            needs_refresh INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            grade TEXT,
            score REAL,
            purpose REAL DEFAULT 0,
            usage_guidelines REAL DEFAULT 0,
            behavior REAL DEFAULT 0,
            parameters REAL DEFAULT 0,
            conciseness REAL DEFAULT 0,
            completeness REAL DEFAULT 0,
            scraped_at TIMESTAMP,
            UNIQUE(repo_id, name)
        );

        CREATE TABLE IF NOT EXISTS refresh_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            repos_attempted INTEGER DEFAULT 0,
            repos_succeeded INTEGER DEFAULT 0,
            repos_failed INTEGER DEFAULT 0,
            errors TEXT
        );

        CREATE TABLE IF NOT EXISTS fleet_repos (
            name TEXT PRIMARY KEY,
            glama_author TEXT DEFAULT 'sandraschi',
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS score_snapshots (
            id TEXT PRIMARY KEY,
            ref_log_id INTEGER REFERENCES refresh_log(id),
            created_at TIMESTAMP NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS score_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT NOT NULL REFERENCES score_snapshots(id),
            repo_name TEXT NOT NULL,
            overall_grade TEXT,
            overall_score REAL,
            tdqs_mean REAL,
            tdqs_min REAL,
            tool_count INTEGER DEFAULT 0,
            worst_tool_name TEXT,
            worst_tool_score REAL,
            UNIQUE(snapshot_id, repo_name)
        );
    """)
    conn.commit()
    conn.close()


def seed_fleet(repos: list[FleetRepo]):
    conn = _get_db()
    for r in repos:
        conn.execute(
            "INSERT OR IGNORE INTO fleet_repos (name, glama_author, active) "
            "VALUES (?, ?, ?)",
            (r.name, r.glama_author, 1 if r.active else 0),
        )
    conn.commit()
    conn.close()


def upsert_repo_score(score: RepoScore) -> int:
    conn = _get_db()
    now = datetime.now(UTC).isoformat()
    conn.execute(
        """INSERT INTO repos
        (name, glama_namespace, glama_slug, overall_grade, overall_score,
         coherence_grade, coherence_disambiguation, coherence_naming,
         coherence_tool_count, coherence_completeness,
         tdqs_grade, tdqs_mean, tdqs_min, maintenance_grade,
         profile_completion, latest_release, last_scraped, needs_refresh)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ON CONFLICT(name) DO UPDATE SET
         overall_grade=excluded.overall_grade,
         overall_score=excluded.overall_score,
         coherence_grade=excluded.coherence_grade,
         coherence_disambiguation=excluded.coherence_disambiguation,
         coherence_naming=excluded.coherence_naming,
         coherence_tool_count=excluded.coherence_tool_count,
         coherence_completeness=excluded.coherence_completeness,
         tdqs_grade=excluded.tdqs_grade,
         tdqs_mean=excluded.tdqs_mean,
         tdqs_min=excluded.tdqs_min,
         maintenance_grade=excluded.maintenance_grade,
         profile_completion=excluded.profile_completion,
         latest_release=excluded.latest_release,
         last_scraped=excluded.last_scraped,
         needs_refresh=0""",
        (
            score.name,
            score.glama_namespace,
            score.glama_slug or score.name,
            score.overall_grade,
            score.overall_score,
            score.coherence.grade,
            score.coherence.disambiguation,
            score.coherence.naming_consistency,
            score.coherence.tool_count,
            score.coherence.completeness,
            score.tdqs_grade,
            score.tdqs_mean,
            score.tdqs_min,
            score.maintenance_grade,
            score.profile_completion,
            score.latest_release,
            now,
        ),
    )
    repo_row = conn.execute(
        "SELECT id FROM repos WHERE name=?", (score.name,)
    ).fetchone()
    repo_id = repo_row["id"]
    conn.execute("DELETE FROM tools WHERE repo_id=?", (repo_id,))
    for t in score.tools:
        conn.execute(
            """INSERT INTO tools
            (repo_id, name, grade, score, purpose, usage_guidelines,
             behavior, parameters, conciseness, completeness, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                repo_id, t.name, t.grade, t.score,
                t.purpose, t.usage_guidelines, t.behavior,
                t.parameters, t.conciseness, t.completeness,
                now,
            ),
        )
    conn.commit()
    conn.close()
    return repo_id


def get_all_repo_scores() -> list[dict]:
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM repos ORDER BY overall_score ASC NULLS LAST, name ASC"
    ).fetchall()
    result = []
    for r in rows:
        tools = conn.execute(
            "SELECT * FROM tools WHERE repo_id=? ORDER BY score ASC, name ASC",
            (r["id"],),
        ).fetchall()
        result.append({
            "id": r["id"],
            "name": r["name"],
            "overall_grade": r["overall_grade"],
            "overall_score": r["overall_score"],
            "tdqs_grade": r["tdqs_grade"],
            "tdqs_mean": r["tdqs_mean"],
            "tdqs_min": r["tdqs_min"],
            "coherence_grade": r["coherence_grade"],
            "maintenance_grade": r["maintenance_grade"],
            "profile_completion": r["profile_completion"],
            "latest_release": r["latest_release"],
            "last_scraped": r["last_scraped"],
            "tools": [dict(t) for t in tools],
        })
    conn.close()
    return result


def get_repo_score(name: str) -> dict | None:
    conn = _get_db()
    r = conn.execute("SELECT * FROM repos WHERE name=?", (name,)).fetchone()
    if not r:
        conn.close()
        return None
    tools = conn.execute(
        "SELECT * FROM tools WHERE repo_id=? ORDER BY score ASC",
        (r["id"],),
    ).fetchall()
    result = dict(r)
    result["tools"] = [dict(t) for t in tools]
    conn.close()
    return result


def get_worst_tools(limit: int = 20) -> list[dict]:
    conn = _get_db()
    rows = conn.execute(
        """SELECT t.name AS tool_name, t.score AS tool_score,
                  t.grade AS tool_grade,
                  r.name AS repo_name, r.overall_grade AS repo_grade
           FROM tools t JOIN repos r ON t.repo_id = r.id
           ORDER BY t.score ASC NULLS LAST
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_refresh_start() -> int:
    conn = _get_db()
    now = datetime.now(UTC).isoformat()
    cur = conn.execute(
        "INSERT INTO refresh_log (started_at) VALUES (?)", (now,)
    )
    log_id = cur.lastrowid
    conn.commit()
    conn.close()
    return log_id


def log_refresh_end(
    log_id: int, attempted: int, succeeded: int, failed: int, errors: list[str]
):
    conn = _get_db()
    conn.execute(
        """UPDATE refresh_log SET
           completed_at=?, repos_attempted=?, repos_succeeded=?,
           repos_failed=?, errors=?
           WHERE id=?""",
        (
            datetime.now(UTC).isoformat(),
            attempted, succeeded, failed,
            json.dumps(errors), log_id,
        ),
    )
    conn.commit()
    conn.close()


def get_refresh_history(limit: int = 10) -> list[dict]:
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM refresh_log ORDER BY started_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_snapshot(ref_log_id: int) -> str:
    """Create a score snapshot from current repos data, return snapshot_id."""
    import uuid

    snapshot_id = str(uuid.uuid4())
    conn = _get_db()
    conn.execute(
        "INSERT INTO score_snapshots (id, ref_log_id) VALUES (?, ?)",
        (snapshot_id, ref_log_id),
    )
    repos = conn.execute("SELECT * FROM repos").fetchall()
    for r in repos:
        tools = conn.execute(
            "SELECT * FROM tools WHERE repo_id=? ORDER BY score ASC LIMIT 1",
            (r["id"],),
        ).fetchall()
        worst = tools[0] if tools else None
        tc_row = conn.execute(
            "SELECT COUNT(*) FROM tools WHERE repo_id=?", (r["id"],)
        ).fetchone()
        tool_count = tc_row[0]
        conn.execute(
            """INSERT INTO score_history
            (snapshot_id, repo_name, overall_grade, overall_score,
             tdqs_mean, tdqs_min, tool_count,
             worst_tool_name, worst_tool_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot_id, r["name"],
                r["overall_grade"], r["overall_score"],
                r["tdqs_mean"], r["tdqs_min"],
                tool_count,
                worst["name"] if worst else None,
                worst["score"] if worst else None,
            ),
        )
    conn.commit()
    conn.close()
    return snapshot_id


def get_latest_snapshots(n: int = 2) -> list[dict]:
    """Return the last N snapshots with their data."""
    conn = _get_db()
    snaps = conn.execute(
        "SELECT * FROM score_snapshots ORDER BY created_at DESC LIMIT ?",
        (n,),
    ).fetchall()
    result = []
    for s in snaps:
        rows = conn.execute(
            "SELECT * FROM score_history WHERE snapshot_id=? "
            "ORDER BY repo_name",
            (s["id"],),
        ).fetchall()
        result.append({
            "snapshot_id": s["id"],
            "created_at": s["created_at"],
            "repos": [dict(r) for r in rows],
        })
    conn.close()
    return result


def compute_deltas() -> list[dict]:
    """Compare latest two snapshots and return per-repo changes."""
    snaps = get_latest_snapshots(2)
    if len(snaps) < 2:
        return []

    curr = {r["repo_name"]: r for r in snaps[0]["repos"]}
    prev = {r["repo_name"]: r for r in snaps[1]["repos"]}
    all_repos = sorted(set(curr) | set(prev))

    deltas = []
    for name in all_repos:
        c = curr.get(name)
        p = prev.get(name)
        if c and p:
            change = round(
                (c["overall_score"] or 0) - (p["overall_score"] or 0), 2
            )
        else:
            change = None
        delta = {
            "repo_name": name,
            "current_grade": c["overall_grade"] if c else None,
            "previous_grade": p["overall_grade"] if p else None,
            "current_score": c["overall_score"] if c else None,
            "previous_score": p["overall_score"] if p else None,
            "score_change": change,
            "current_tdqs_mean": c["tdqs_mean"] if c else None,
            "previous_tdqs_mean": p["tdqs_mean"] if p else None,
            "current_worst_tool": c["worst_tool_name"] if c else None,
            "previous_worst_tool": p["worst_tool_name"] if p else None,
            "new": c and not p,
            "removed": p and not c,
        }
        deltas.append(delta)
    return deltas


def generate_report() -> dict:
    """Generate a daily status report with current scores and deltas."""
    repos = get_all_repo_scores()
    deltas = compute_deltas()
    latest = get_latest_snapshots(1)
    snapshot_time = latest[0]["created_at"] if latest else None

    grades: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0, "none": 0}
    for r in repos:
        g = r.get("overall_grade") or "none"
        grades[g] = grades.get(g, 0) + 1

    worst_tools = get_worst_tools(5)
    stale = []
    now = datetime.now(UTC)
    for r in repos:
        if r.get("last_scraped"):
            try:
                ts = datetime.fromisoformat(r["last_scraped"])
                days = (now - ts).days
                if days > 7:
                    stale.append({"name": r["name"], "days": days})
            except ValueError:
                pass

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "snapshot_time": snapshot_time,
        "total_repos": len(repos),
        "grade_distribution": grades,
        "repos": repos,
        "deltas": deltas,
        "worst_tools_fleet": worst_tools,
        "stale_repos": stale,
    }
