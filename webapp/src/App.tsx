import React, { useEffect, useState, useCallback } from "react";
import ScoreTable from "./components/ScoreTable";
import ToolBreakdown from "./components/ToolBreakdown";
import RefreshPanel from "./components/RefreshPanel";

type Repo = Record<string, unknown>;
type View = "table" | "detail";

export default function App() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>("table");
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchRepos = useCallback(async () => {
    try {
      setLoading(true);
      const r = await fetch("/api/repos");
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setRepos(Array.isArray(data) ? data : []);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load repos");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRepos();
  }, [fetchRepos, refreshKey]);

  const handleRefresh = () => setRefreshKey((k) => k + 1);
  const handleSelectRepo = (name: string) => {
    setSelectedRepo(name);
    setView("detail");
  };
  const handleBack = () => {
    setView("table");
    setSelectedRepo(null);
  };

  const gradeCounts = { A: 0, B: 0, C: 0, D: 0, F: 0, none: 0 };
  for (const r of repos) {
    const g = (r.overall_grade as string) || "none";
    gradeCounts[g as keyof typeof gradeCounts] =
      (gradeCounts[g as keyof typeof gradeCounts] || 0) + 1;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              Glama Status
            </h1>
            <p className="text-sm text-gray-500">
              Fleet score dashboard  -  {repos.length} repos tracked
            </p>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-emerald-400">{gradeCounts.A}A</span>
            <span className="text-blue-400">{gradeCounts.B}B</span>
            <span className="text-amber-400">{gradeCounts.C}C</span>
            <span className="text-orange-400">{gradeCounts.D}D</span>
            <span className="text-red-400">{gradeCounts.F}F</span>
            <span className="text-gray-600">{gradeCounts.none}?</span>
            <RefreshPanel onRefresh={handleRefresh} />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {error && (
          <div className="bg-red-900/50 border border-red-700 rounded px-4 py-3 mb-4 text-sm">
            {error}
            <button
              type="button"
              onClick={handleRefresh}
              className="ml-3 underline hover:text-red-300"
            >
              Retry
            </button>
          </div>
        )}

        {loading && repos.length === 0 && (
          <div className="text-center py-20 text-gray-600">
            Loading scores...
          </div>
        )}

        {!loading && repos.length === 0 && !error && (
          <div className="text-center py-20 text-gray-500">
            <p className="text-lg mb-2">No scores yet</p>
            <p className="text-sm">
              Click{" "}
              <button
                type="button"
                onClick={handleRefresh}
                className="text-blue-400 underline"
              >
                Refresh Now
              </button>{" "}
              to scrape Glama and populate the database.
            </p>
          </div>
        )}

        {view === "detail" && selectedRepo ? (
          <ToolBreakdown repoName={selectedRepo} onBack={handleBack} />
        ) : (
          repos.length > 0 && (
            <ScoreTable repos={repos} onSelectRepo={handleSelectRepo} />
          )
        )}
      </main>

      <footer className="border-t border-gray-800 px-6 py-3 text-xs text-gray-600 text-center">
        Data sourced from{" "}
        <a
          href="https://glama.ai/mcp/servers"
          className="underline hover:text-gray-400"
          target="_blank"
          rel="noopener noreferrer"
        >
          glama.ai
        </a>{" "}
        &middot; Refreshed daily &middot;{" "}
        <button
          type="button"
          onClick={handleRefresh}
          className="underline hover:text-gray-400"
        >
          Refresh now
        </button>
      </footer>
    </div>
  );
}
