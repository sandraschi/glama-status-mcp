"""Database operations tests."""

from glama_status_mcp.database import (
    init_db,
    seed_fleet,
    upsert_repo_score,
    get_all_repo_scores,
    get_repo_score,
    get_worst_tools,
    log_refresh_start,
    log_refresh_end,
    get_refresh_history,
    create_snapshot,
    compute_deltas,
    generate_report,
)
from glama_status_mcp.models import FleetRepo


class TestDatabase:
    def test_init_db_creates_tables(self, temp_data_dir):
        init_db()
        db = temp_data_dir / "test_glama_status.db"
        assert db.exists()
        assert db.stat().st_size > 0

    def test_seed_fleet_inserts_repos(self, temp_data_dir, fleet_repos):
        init_db()
        seed_fleet(fleet_repos)
        repos = get_all_repo_scores()
        # fleet_repos seeds into fleet_repos table, not repos table
        # repos table is populated by upsert_repo_score
        assert len(repos) == 0  # No scores yet

    def test_upsert_and_get_repo_score(self, temp_data_dir, sample_repo_score):
        init_db()
        repo_id = upsert_repo_score(sample_repo_score)
        assert repo_id > 0

        result = get_repo_score("test-mcp")
        assert result is not None
        assert result["overall_grade"] == "A"
        assert len(result["tools"]) == 2

        scores = get_all_repo_scores()
        assert len(scores) == 1
        assert scores[0]["name"] == "test-mcp"

    def test_upsert_repo_score_updates_existing(
        self, temp_data_dir, sample_repo_score
    ):
        from glama_status_mcp.models import RepoScore, ToolScore, ServerCoherence

        init_db()
        upsert_repo_score(sample_repo_score)

        updated = RepoScore(
            name="test-mcp",
            overall_grade="B",
            overall_score=3.0,
            tdqs_mean=3.2,
            tdqs_min=2.8,
            coherence=ServerCoherence(grade="B"),
            tools=[ToolScore(name="new_tool", grade="C", score=2.5)],
        )
        upsert_repo_score(updated)

        result = get_repo_score("test-mcp")
        assert result["overall_grade"] == "B"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "new_tool"

    def test_get_nonexistent_repo(self, temp_data_dir):
        init_db()
        result = get_repo_score("nonexistent")
        assert result is None

    def test_get_worst_tools(self, temp_data_dir, sample_repo_score):
        init_db()
        upsert_repo_score(sample_repo_score)
        worst = get_worst_tools(5)
        assert len(worst) == 2
        # Sorted worst first
        assert worst[0]["tool_score"] <= worst[1]["tool_score"]

    def test_worst_tools_empty_db(self, temp_data_dir):
        init_db()
        worst = get_worst_tools(10)
        assert worst == []

    def test_refresh_log(self, temp_data_dir):
        init_db()
        log_id = log_refresh_start()
        assert log_id > 0

        log_refresh_end(log_id, 10, 8, 2, ["repo1: error"])
        history = get_refresh_history(5)
        assert len(history) == 1
        assert history[0]["repos_attempted"] == 10
        assert history[0]["repos_succeeded"] == 8

    def test_snapshot_and_deltas(self, temp_data_dir, sample_repo_score):
        from glama_status_mcp.models import RepoScore, ToolScore, ServerCoherence

        init_db()
        log_id = log_refresh_start()
        upsert_repo_score(sample_repo_score)
        log_refresh_end(log_id, 1, 1, 0, [])

        snap1 = create_snapshot(log_id)
        assert snap1 is not None

        # Second refresh with updated score
        log_id2 = log_refresh_start()
        updated = RepoScore(
            name="test-mcp",
            overall_grade="B",
            overall_score=3.5,
            tdqs_mean=3.5,
            tdqs_min=3.0,
            coherence=ServerCoherence(grade="B"),
            tools=[ToolScore(name="t1", grade="B", score=3.5)],
        )
        upsert_repo_score(updated)
        log_refresh_end(log_id2, 1, 1, 0, [])
        create_snapshot(log_id2)

        deltas = compute_deltas()
        assert len(deltas) >= 1
        test_delta = next(d for d in deltas if d["repo_name"] == "test-mcp")
        assert test_delta["score_change"] is not None

    def test_generate_report(self, temp_data_dir, sample_repo_score):
        init_db()
        upsert_repo_score(sample_repo_score)
        report = generate_report()
        assert report["total_repos"] == 1
        assert report["grade_distribution"]["A"] == 1
        assert "repos" in report
        assert "deltas" in report

    def test_get_all_repo_scores_empty(self, temp_data_dir):
        init_db()
        repos = get_all_repo_scores()
        assert repos == []

    def test_get_all_repo_scores_sorted(self, temp_data_dir):
        from glama_status_mcp.models import RepoScore, ToolScore, ServerCoherence

        init_db()
        for name, score in [("c-repo", 2.0), ("a-repo", 4.0), ("b-repo", 3.0)]:
            r = RepoScore(
                name=name,
                overall_score=score,
                overall_grade="B",
                coherence=ServerCoherence(),
                tools=[],
            )
            upsert_repo_score(r)

        repos = get_all_repo_scores()
        assert len(repos) == 3
        # Worst first
        assert repos[0]["name"] == "c-repo"
        assert repos[2]["name"] == "a-repo"
