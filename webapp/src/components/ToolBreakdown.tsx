import React, { useEffect, useState } from "react";

interface Tool {
  name: string;
  grade: string;
  score: number;
  purpose: number;
  usage_guidelines: number;
  behavior: number;
  parameters: number;
  conciseness: number;
  completeness: number;
}

interface RepoDetail {
  name: string;
  overall_grade: string;
  overall_score: number;
  tdqs_grade: string;
  tdqs_mean: number;
  tdqs_min: number;
  coherence_grade: string;
  coherence_disambiguation: number;
  coherence_naming: number;
  coherence_tool_count: number;
  coherence_completeness: number;
  maintenance_grade: string;
  profile_completion: number;
  latest_release: string;
  last_scraped: string;
  tools: Tool[];
}

function gradeColor(grade: string | null): string {
  switch (grade) {
    case "A": return "text-emerald-400";
    case "B": return "text-blue-400";
    case "C": return "text-amber-400";
    case "D": return "text-orange-400";
    case "F": return "text-red-400";
    default: return "text-gray-600";
  }
}

function dimBar(val: number): string {
  const pct = (val / 5) * 100;
  const color =
    val >= 4 ? "bg-emerald-500" : val >= 3 ? "bg-blue-500" : val >= 2 ? "bg-amber-500" : "bg-red-500";
  return `<div class="w-16 bg-gray-800 rounded-full h-1.5 inline-block align-middle"><div class="h-1.5 rounded-full ${color}" style="width:${pct}%"></div></div>`;
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
    (async () => {
      try {
        setLoading(true);
        const r = await fetch(`/api/repos/${repoName}`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        setRepo(await r.json());
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load repo");
      } finally {
        setLoading(false);
      }
    })();
  }, [repoName]);

  if (loading) {
    return <div className="text-center py-12 text-gray-600">Loading...</div>;
  }

  if (error || !repo) {
    return (
      <div className="text-center py-12">
        <p className="text-red-400 mb-2">{error || "Repo not found"}</p>
        <button type="button" onClick={onBack} className="text-blue-400 underline text-sm">
          Back to table
        </button>
      </div>
    );
  }

  const sortedTools = [...repo.tools].sort((a, b) => a.score - b.score);
  const worstScore = sortedTools[0]?.score || 0;
  const bestScore = sortedTools[sortedTools.length - 1]?.score || 0;

  return (
    <div>
      <button
        type="button"
        onClick={onBack}
        className="text-blue-400 hover:text-blue-300 text-sm mb-4 inline-block"
      >
        &larr; Back to table
      </button>

      <div className="bg-gray-900 rounded-lg border border-gray-800 p-5 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold">{repo.name}</h2>
            <p className="text-sm text-gray-500">
              Last scraped: {repo.last_scraped ? new Date(repo.last_scraped).toLocaleString() : "never"}
              &middot; Release: {repo.latest_release || "—"}
            </p>
          </div>
          <div className="text-right">
            <span className={`text-2xl font-bold ${gradeColor(repo.overall_grade)}`}>
              {repo.overall_grade || "—"}
            </span>
            <span className="text-gray-500 text-sm ml-1">
              {repo.overall_score?.toFixed(2)}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">TDQS</span>
            <span className={`ml-2 font-medium ${gradeColor(repo.tdqs_grade)}`}>
              {repo.tdqs_grade || "—"}
            </span>
            <div className="text-xs text-gray-600">
              μ={repo.tdqs_mean?.toFixed(2)} min={repo.tdqs_min?.toFixed(2)}
            </div>
          </div>
          <div>
            <span className="text-gray-500">Coherence</span>
            <span className={`ml-2 font-medium ${gradeColor(repo.coherence_grade)}`}>
              {repo.coherence_grade || "—"}
            </span>
            <div className="text-xs text-gray-600">
              D={repo.coherence_disambiguation?.toFixed(1)} N={repo.coherence_naming?.toFixed(1)}
              &nbsp;T={repo.coherence_tool_count?.toFixed(1)} C={repo.coherence_completeness?.toFixed(1)}
            </div>
          </div>
          <div>
            <span className="text-gray-500">Maintenance</span>
            <span className={`ml-2 font-medium ${gradeColor(repo.maintenance_grade)}`}>
              {repo.maintenance_grade || "—"}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Profile</span>
            <span className="ml-2 font-medium">{repo.profile_completion || 0}%</span>
          </div>
        </div>
      </div>

      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
        Tools ({repo.tools.length}) &middot; range: {worstScore.toFixed(1)}–{bestScore.toFixed(1)}
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
          const avgDim = dims.reduce((s, d) => s + d.val, 0) / dims.length;

          return (
            <div
              key={tool.name}
              className="bg-gray-900/50 border border-gray-800 rounded-lg px-4 py-3"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm">{tool.name}</span>
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
                  <span className="text-sm text-gray-400">{tool.score.toFixed(1)}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
                {dims.map((d) => {
                  const pct = (d.val / 5) * 100;
                  const barColor =
                    d.val >= 4 ? "bg-emerald-500" : d.val >= 3 ? "bg-blue-500" : d.val >= 2 ? "bg-amber-500" : "bg-red-500";
                  return (
                    <div key={d.label} className="flex items-center gap-1.5">
                      <span className="text-gray-500 w-14">{d.label}</span>
                      <div className="w-12 bg-gray-800 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${barColor}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-gray-400 w-3">{d.val.toFixed(1)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {repo.overall_score < 3.5 && (
        <div className="mt-6 bg-blue-900/20 border border-blue-800/50 rounded-lg px-4 py-3 text-sm">
          <p className="text-blue-300 font-medium mb-1">Improvement hint</p>
          <p className="text-blue-200/70 text-xs">
            The lowest-scoring tool ({sortedTools[0]?.name}, {sortedTools[0]?.score?.toFixed(1)}/5)
            pulls down the entire server (60% mean + 40% minimum weighting).
            Fix its docstrings — add missing parameter descriptions via{" "}
            <code className="text-blue-300">Field(description=...)</code>,
            behavioral warnings for destructive ops, and usage guidance —
            then make a release and trigger Sync Server on glama.ai.
          </p>
        </div>
      )}
    </div>
  );
}
