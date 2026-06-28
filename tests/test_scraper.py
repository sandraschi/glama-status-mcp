"""HTML scraper tests with mock responses."""

import pytest

from glama_status_mcp.scraper import _parse_html, _parse_grade, _parse_score


class TestParser:
    def test_parse_grade_valid(self):
        assert _parse_grade("Grade: A (4.5/5)") == "A"
        assert _parse_grade("F") == "F"

    def test_parse_grade_invalid(self):
        assert _parse_grade("No grade here") == ""

    def test_parse_score_valid(self):
        assert _parse_score("4.5 / 5") == 4.5
        assert _parse_score("3/5") == 3.0
        assert _parse_score("0.0/5") == 0.0

    def test_parse_score_invalid(self):
        assert _parse_score("no score") == 0.0

    def test_parse_html_profile_completion(self):
        html = "<html><body><div>75% profile complete</div></body></html>"
        result = _parse_html(html, "test", "sandraschi")
        assert result.name == "test"
        assert result.profile_completion == 75

    def test_parse_html_latest_release(self):
        html = "<html><body><div>Latest release v1.2.3-beta</div></body></html>"
        result = _parse_html(html, "test", "sandraschi")
        assert result.latest_release == "v1.2.3-beta"

    def test_parse_html_grade_badges(self):
        html = """<html><body>
            <div><span class="kIIaya">A</span>Server Coherence</div>
            <div><span class="kIIaya">B</span>Maintenance</div>
            <div><span class="kIIaya">C</span>Tool Definition Quality</div>
        </body></html>"""
        result = _parse_html(html, "test", "sandraschi")
        assert result.coherence.grade == "A"
        assert result.maintenance_grade == "B"
        assert result.tdqs_grade == "C"

    def test_parse_html_tdqs_scores(self):
        html = """<html><body>
            <p>Average 4.2 / 5 Lowest: 3.5 / 5</p>
        </body></html>"""
        result = _parse_html(html, "test", "sandraschi")
        assert result.tdqs_mean == 4.2
        assert result.tdqs_min == 3.5
        expected = round(0.6 * 4.2 + 0.4 * 3.5, 2)
        assert result.overall_score == expected

    def test_parse_html_coherence_sub_scores(self):
        html = """<html><body>
            <div>
                <span>Disambiguation</span>
                <span class="czikZZ">4.0 / 5</span>
            </div>
            <div>
                <span>Naming Consistency</span>
                <span class="czikZZ">3.5 / 5</span>
            </div>
        </body></html>"""
        result = _parse_html(html, "test", "sandraschi")
        assert result.coherence.disambiguation == 4.0
        assert result.coherence.naming_consistency == 3.5

    def test_parse_html_tool_cards(self):
        html = """<html><body>
            <button class="ULqjq">
                <a href="/tools/tool1">tool1</a> A 4.5 / 5
            </button>
            <div>
                <div>Purpose</div>
                <div class="gMBAYo"><span class="czikZZ">4.0 / 5</span></div>
                <div>Usage Guidelines</div>
                <div class="gMBAYo"><span class="czikZZ">3.5 / 5</span></div>
            </div>
        </body></html>"""
        result = _parse_html(html, "test", "sandraschi")
        assert len(result.tools) == 1
        assert result.tools[0].name == "tool1"
        assert result.tools[0].grade == "A"
        assert result.tools[0].score == 4.5

    def test_parse_html_no_grades(self):
        """Empty page returns default RepoScore with no tools."""
        html = "<html><body></body></html>"
        result = _parse_html(html, "test", "sandraschi")
        assert result.name == "test"
        assert result.tools == []
        assert result.overall_grade == ""

    def test_parse_html_fallback_overall(self):
        """When TDQS section is missing, compute overall from tool scores."""
        html = """<html><body>
            <button class="ULqjq">
                <a href="/tools/t1">t1</a> A 4.0 / 5
            </button>
            <div></div>
            <button class="ULqjq">
                <a href="/tools/t2">t2</a> B 3.0 / 5
            </button>
            <div></div>
        </body></html>"""
        result = _parse_html(html, "test", "sandraschi")
        assert result.overall_score > 0
        assert result.overall_grade in ("A", "B", "C", "D", "F")


class TestScraperIntegration:
    """Integration-style tests using respx to mock HTTP."""

    @pytest.mark.asyncio
    async def test_scrape_repo_404(self):
        """Scraper returns None on 404."""
        import respx
        from glama_status_mcp.scraper import scrape_repo

        async with respx.mock() as mock:
            mock.get(
                "https://glama.ai/mcp/servers/sandraschi/no-repo/score",
            ).respond(404)
            result = await scrape_repo("no-repo")
            assert result is None

    @pytest.mark.asyncio
    async def test_scrape_repo_success(self):
        """Scraper returns RepoScore on successful fetch."""
        import respx
        from glama_status_mcp.scraper import scrape_repo

        html = """<html><body>
            <div>100% profile complete</div>
            <div>Latest release v2.0.0</div>
            <div><span class="kIIaya">A</span>Server Coherence</div>
            <div><span class="kIIaya">A</span>Maintenance</div>
            <div><span class="kIIaya">B</span>Tool Definition Quality</div>
            <p>Average 4.0 / 5 Lowest: 3.2 / 5</p>
            <button class="ULqjq">
                <a href="/tools/test_tool">test_tool</a> B 3.8 / 5
            </button>
            <div>
                <div>Purpose</div>
                <div class="gMBAYo"><span class="czikZZ">4.0 / 5</span></div>
            </div>
        </body></html>"""

        async with respx.mock() as mock:
            mock.get(
                "https://glama.ai/mcp/servers/sandraschi/test-repo/score",
            ).respond(200, text=html)
            result = await scrape_repo("test-repo")
            assert result is not None
            assert result.name == "test-repo"
            assert result.profile_completion == 100
            assert result.latest_release == "v2.0.0"
            assert result.coherence.grade == "A"
            assert result.tdqs_grade == "B"
            assert len(result.tools) == 1

    @pytest.mark.asyncio
    async def test_scrape_repo_connection_error(self):
        """Scraper returns None on connection error."""
        import respx
        from glama_status_mcp.scraper import scrape_repo

        async with respx.mock() as mock:
            mock.get(
                "https://glama.ai/mcp/servers/sandraschi/test-repo/score",
            ).mock(side_effect=Exception("Connection refused"))
            result = await scrape_repo("test-repo")
            assert result is None
