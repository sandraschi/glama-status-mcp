import React, { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  LayoutDashboard,
  MessageSquare,
  RefreshCw,
  Server,
  Settings,
  Wrench,
} from "lucide-react";
import { useStore } from "./store";
import type { Repo } from "./types";
import { Sidebar } from "./components/Sidebar";
import ScoreTable from "./components/ScoreTable";
import ToolBreakdown from "./components/ToolBreakdown";
import ReportView from "./components/ReportView";
import { HelpPage } from "./components/HelpPage";
import { ToolsPage } from "./components/ToolsPage";
import { SettingsPage } from "./components/SettingsPage";
import { ChatPage } from "./components/ChatPage";

function gradeCounts(repos: { overall_grade?: string }[]) {
  const gc: Record<string, number> = {
    A: 0, B: 0, C: 0, D: 0, F: 0, none: 0,
  };
  for (const r of repos) {
    const g = r.overall_grade || "none";
    gc[g] = (gc[g] || 0) + 1;
  }
  return gc;
}

function Hero({ repos }: { repos: Repo[] }) {
  const gc = gradeCounts(repos);
  const scored = gc.A + gc.B + gc.C + gc.D + gc.F;
  const stale = repos.filter((r) => {
    if (!r.last_scraped) return false;
    const days = Math.floor((Date.now() - new Date(r.last_scraped).getTime()) / 86400000);
    return days > 7;
  }).length;
  const worstRepo = [...repos].sort((a, b) => (a.overall_score ?? 999) - (b.overall_score ?? 999))[0];
  const totalTools = repos.reduce((s, r) => s + (r.tools?.length ?? 0), 0);
  const worstTool = repos
    .flatMap((r) => (r.tools ?? []).map((t) => ({ ...t, repo: r.name })))
    .sort((a, b) => (a.score ?? 5) - (b.score ?? 5))[0];

  return (
    <div className="bg-gradient-to-r from-zinc-900 via-zinc-900/80 to-zinc-950 rounded-xl border border-zinc-800 p-6 mb-6">
      <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
        Glama Fleet Dashboard
      </h1>
      <p className="text-sm text-zinc-400 mt-1">
        {scored} repos scored &middot; {totalTools} tools &middot;{" "}
        {stale > 0 ? `${stale} stale` : "all fresh"}
      </p>
      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-zinc-800">
        <div>
          <div className="text-xs text-zinc-400 uppercase tracking-wider">
            Grade Spread
          </div>
          <div className="mt-1 text-sm flex gap-2">
            <span className="text-emerald-400 font-medium">A {gc.A}</span>
            <span className="text-blue-400 font-medium">B {gc.B}</span>
            <span className="text-amber-400 font-medium">C {gc.C}</span>
            <span className="text-orange-400 font-medium">D {gc.D}</span>
            <span className="text-red-400 font-medium">F {gc.F}</span>
          </div>
        </div>
        <div>
          <div className="text-xs text-zinc-400 uppercase tracking-wider">
            Weakest Link
          </div>
          <div className="mt-1 text-sm">
            {worstRepo ? (
              <>
                <span className="text-zinc-300">{worstRepo.name}</span>
                <span className="text-zinc-400 ml-1">
                  ({worstRepo.overall_score?.toFixed(2) ?? "?"})
                </span>
              </>
            ) : (
              <span className="text-zinc-400">N/A</span>
            )}
          </div>
        </div>
        <div>
          <div className="text-xs text-zinc-400 uppercase tracking-wider">
            Worst Tool
          </div>
          <div className="mt-1 text-sm">
            {worstTool ? (
              <>
                <span className="text-zinc-300">{worstTool.name}</span>
                <span className="text-zinc-400 ml-1">
                  {worstTool.score?.toFixed(1)}/5 in {worstTool.repo}
                </span>
              </>
            ) : (
              <span className="text-zinc-400">N/A</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const PAGE_META: Record<string, { icon: typeof LayoutDashboard; title: string }> = {
  dashboard: { icon: LayoutDashboard, title: "Dashboard" },
  detail: { icon: LayoutDashboard, title: "Repo Detail" },
  report: { icon: BarChart3, title: "Daily Fleet Report" },
  tools: { icon: Wrench, title: "Tools Overview" },
  chat: { icon: MessageSquare, title: "Chat" },
  settings: { icon: Settings, title: "Settings" },
  help: { icon: Server, title: "Help & Documentation" },
};

export default function App() {
  const {
    repos,
    loading,
    error,
    page,
    selectedRepo,
    fetchRepos,
    setPage,
    setSelectedRepo,
  } = useStore();
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchRepos();
  }, [fetchRepos]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const r = await fetch("/api/refresh", { method: "POST" });
      await r.json();
    } catch {
      /* silent */
    } finally {
      await fetchRepos();
      setRefreshing(false);
    }
  }, [fetchRepos]);

  const gc = gradeCounts(repos);
  const meta = PAGE_META[selectedRepo ? "detail" : page] || PAGE_META.dashboard;
  const PageIcon = meta.icon;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex">
      <Sidebar
        activePage={selectedRepo ? "detail" : page}
        onNavigate={(p) => {
          setPage(p as "dashboard" | "report" | "tools" | "chat" | "help" | "settings");
        }}
        onRefresh={handleRefresh}
        refreshing={refreshing}
        repoCount={repos.length}
        gradeCounts={gc}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="border-b border-zinc-800 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <PageIcon className="w-4 h-4 text-zinc-400" />
            {selectedRepo ? (
              <>
                <button
                  type="button"
                  onClick={() => setSelectedRepo(null)}
                  className="text-zinc-400 hover:text-zinc-300"
                >
                  Dashboard
                </button>
                <span className="text-zinc-400">/</span>
                <span className="text-zinc-400">{selectedRepo}</span>
              </>
            ) : (
              <span className="text-zinc-400">{meta.title}</span>
            )}
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="text-emerald-400">A {gc.A}</span>
            <span className="text-blue-400">B {gc.B}</span>
            <span className="text-amber-400">C {gc.C}</span>
            <span className="text-orange-400">D {gc.D}</span>
            <span className="text-red-400">F {gc.F}</span>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 px-6 py-6 overflow-auto">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-900/50 border border-red-700 rounded px-4 py-3 mb-4 text-sm"
            >
              {error}
              <button
                type="button"
                onClick={handleRefresh}
                className="ml-3 underline hover:text-red-300"
              >
                <RefreshCw className="w-3.5 h-3.5 inline" /> Retry
              </button>
            </motion.div>
          )}

          {loading && repos.length === 0 && (
            <div className="text-center py-20 text-zinc-400">
              <RefreshCw className="w-8 h-8 mx-auto mb-4 animate-spin" />
              Loading scores...
            </div>
          )}

          {!loading && repos.length === 0 && !error && (
            <div className="text-center py-20 text-zinc-400">
              <Server className="w-12 h-12 mx-auto mb-4 text-zinc-700" />
              <p className="text-lg mb-2">No scores yet</p>
              <p className="text-sm">
                Click Refresh in the sidebar or run{" "}
                <code className="text-zinc-400">just refresh</code> to
                populate the database.
              </p>
            </div>
          )}

          <AnimatePresence mode="wait">
            {selectedRepo ? (
              <motion.div
                key="detail"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <ToolBreakdown
                  repoName={selectedRepo}
                  onBack={() => setSelectedRepo(null)}
                />
              </motion.div>
            ) : page === "report" ? (
              <motion.div
                key="report"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <ReportView onBack={() => setPage("dashboard")} />
              </motion.div>
            ) : page === "tools" ? (
              <motion.div
                key="tools"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <ToolsPage />
              </motion.div>
            ) : page === "help" ? (
              <motion.div
                key="help"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <HelpPage />
              </motion.div>
            ) : page === "chat" ? (
              <motion.div
                key="chat"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <ChatPage />
              </motion.div>
            ) : page === "settings" ? (
              <motion.div
                key="settings"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <SettingsPage />
              </motion.div>
            ) : (
              repos.length > 0 && (
                <motion.div
                  key="dashboard"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <Hero repos={repos} />
                  <ScoreTable
                    repos={repos}
                    onSelectRepo={(name) => setSelectedRepo(name)}
                  />
                </motion.div>
              )
            )}
          </AnimatePresence>
        </main>

        <footer className="border-t border-zinc-800 px-6 py-3 text-xs text-zinc-400 text-center">
          Data sourced from{" "}
          <a
            href="https://glama.ai/mcp/servers"
            className="underline hover:text-zinc-400"
            target="_blank"
            rel="noopener noreferrer"
          >
            glama.ai
          </a>{" "}
          &middot; Refreshed daily &middot;{" "}
          <button
            type="button"
            onClick={handleRefresh}
            className="underline hover:text-zinc-400"
          >
            Refresh now
          </button>
        </footer>
      </div>
    </div>
  );
}
