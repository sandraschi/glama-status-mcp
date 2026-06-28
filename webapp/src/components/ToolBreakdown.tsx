import React, { useEffect, useState } from "react";
import { AlertTriangle, ArrowLeft, ExternalLink } from "lucide-react";
import type { Repo as RepoDetail, Tool } from "../types";

function ghAccount(): string {
  try { return localStorage.getItem("glama-status-gh-account") || "sandraschi"; } catch { return "sandraschi"; }
}

function gradeColor(grade: string | null | undefined): string {
  switch (grade) {
    case "A": return "text-emerald-400";
    case "B": return "text-blue-400";
    case "C": return "text-amber-400";
    case "D": return "text-orange-400";
    case "F": return "text-red-400";
    default: return "text-zinc-400";
  }
}

function dimBar(dims: { label: string; val: number }[]) {
  return dims.map((d) => {
    const pct = (d.val / 5) * 100;
    const barColor =
      d.val >= 4
        ? "bg-emerald-500"
        : d.val >= 3
          ? "bg-blue-500"
          : d.val >= 2
            ? "bg-amber-500"
            : "bg-red-500";
    return (
      <div key={d.label} className="flex items-center gap-1.5">
        <span className="text-zinc-400 w-14 text-xs">{d.label}</span>
        <div className="w-12 bg-zinc-800 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full ${barColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <span className="text-zinc-400 w-3 text-xs">
          {d.val.toFixed(1)}
        </span>
      </div>
    );
  });
}

interface Props {
  repoName: string;
  onBack: () => void;
}

export default function ToolBreakdown({ repoName, onBack }: Props) {
  const [repo, setRepo] = useState<RepoDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const r = await fetch(`/api/repos/${repoName}`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        if (!cancelled) setRepo(data);
      } catch (e: unknown) {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [repoName]);

  if (loading) {
    return (
      <div className="text-center py-12 text-zinc-400">Loading...</div>
    );
  }

  if (error || !repo) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-red-400" />
        <p className="text-red-400 mb-2">{error || "Repo not found"}</p>
        <button
          type="button"
          onClick={onBack}
          className="text-blue-400 underline text-sm"
        >
          Back to table
        </button>
      </div>
    );
  }

  const sortedTools = [...(repo.tools || [])].sort((a, b) => (a.score || 0) - (b.score || 0));
  const worstScore = sortedTools[0]?.score || 0;
  const bestScore = sortedTools[sortedTools.length - 1]?.score || 0;

  return (
    <div>
      <button
        type="button"
        onClick={onBack}
        className="text-blue-400 hover:text-blue-300 text-sm mb-4 inline-flex items-center gap-1"
      >
        <ArrowLeft className="w-3.5 h-3.5" /> Back to table
      </button>

      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold">{repo.name}</h2>
            <p className="text-sm text-zinc-400">
              Last scraped:{" "}
              {repo.last_scraped
                ? new Date(repo.last_scraped).toLocaleString()
                : "never"}
              &middot; Release: {repo.latest_release || "\u2014"}
            </p>
          </div>
          <div className="text-right">
            <span
              className={`text-2xl font-bold ${gradeColor(repo.overall_grade)}`}
            >
              {repo.overall_grade || "\u2014"}
            </span>
            <span className="text-zinc-400 text-sm ml-1">
              {repo.overall_score?.toFixed(2)}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-zinc-400">TDQS</span>
            <span
              className={`ml-2 font-medium ${gradeColor(repo.tdqs_grade)}`}
            >
              {repo.tdqs_grade || "\u2014"}
            </span>
            <div className="text-xs text-zinc-400">
              μ={repo.tdqs_mean?.toFixed(2)} min={repo.tdqs_min?.toFixed(2)}
            </div>
          </div>
          <div>
            <span className="text-zinc-400">Coherence</span>
            <span
              className={`ml-2 font-medium ${gradeColor(repo.coherence_grade)}`}
            >
              {repo.coherence_grade || "\u2014"}
            </span>
            <div className="text-xs text-zinc-400">
              D={repo.coherence_disambiguation?.toFixed(1)}{" "}
              N={repo.coherence_naming?.toFixed(1)}{" "}
              T={repo.coherence_tool_count?.toFixed(1)}{" "}
              C={repo.coherence_completeness?.toFixed(1)}
            </div>
          </div>
          <div>
            <span className="text-zinc-400">Maintenance</span>
            <span
              className={`ml-2 font-medium ${gradeColor(repo.maintenance_grade)}`}
            >
              {repo.maintenance_grade || "\u2014"}
            </span>
          </div>
          <div>
            <span className="text-zinc-400">Profile</span>
            <span className="ml-2 font-medium">
              {repo.profile_completion || 0}%
            </span>
          </div>
        </div>
      </div>

      <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
        Tools ({(repo.tools || []).length}) &middot; range:{" "}
        {worstScore.toFixed(1)}\u2013{bestScore.toFixed(1)}
      </h3>

      <div className="space-y-2">
        {sortedTools.map((tool) => {
          const dims = [
            { label: "Purpose", val: tool.purpose },
            { label: "Usage", val: tool.usage_guidelines },
            { label: "Behavior", val: tool.behavior },
            { label: "Params", val: tool.parameters },
            { label: "Conciseness", val: tool.conciseness },
            { label: "Completeness", val: tool.completeness },
          ];

          return (
            <div
              key={tool.name}
              className="bg-zinc-900/50 border border-zinc-800 rounded-lg px-4 py-3"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <a
                    href={`https://glama.ai/mcp/servers/${ghAccount()}/${repoName}/tools/${encodeURIComponent(tool.name)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-sm text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1"
                    title="Open Glama tool detail"
                  >
                    {tool.name}
                    <ExternalLink className="w-3 h-3 text-zinc-400" />
                  </a>
                  {tool.score < 3 && (
                    <span className="text-xs bg-red-900/50 text-red-300 px-1.5 py-0.5 rounded">
                      needs work
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`font-bold ${gradeColor(tool.grade)}`}>
                    {tool.grade}
                  </span>
                  <span className="text-sm text-zinc-400">
                    {tool.score.toFixed(1)}
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-1">
                {dimBar(dims)}
              </div>
            </div>
          );
        })}
      </div>

      {repo.overall_score != null && repo.overall_score < 3.5 && (
        <div className="mt-6 bg-blue-900/20 border border-blue-800/50 rounded-lg px-4 py-3 text-sm">
          <p className="text-blue-300 font-medium mb-1">
            Improvement hint
          </p>
          <p className="text-blue-200/70 text-xs">
            The lowest-scoring tool ({sortedTools[0]?.name},{" "}
            {sortedTools[0]?.score?.toFixed(1)}/5) pulls down the
            entire server (60% mean + 40% minimum weighting). Fix its
            docstrings -- add missing parameter descriptions via{" "}
            <code className="text-blue-300">
              Field(description=...)
            </code>
            , behavioral warnings for destructive ops, and usage
            guidance -- then make a release and trigger Sync Server on
            glama.ai.
          </p>
        </div>
      )}
    </div>
  );
}
