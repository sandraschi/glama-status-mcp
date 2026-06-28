import React, { useEffect, useState } from "react";
import { ArrowLeft, TrendingDown, TrendingUp } from "lucide-react";

interface Delta {
  repo_name: string;
  current_grade: string;
  previous_grade: string;
  current_score: number;
  previous_score: number;
  score_change: number;
  current_worst_tool: string;
  new: boolean;
  removed: boolean;
}

interface WorstTool {
  tool_name: string;
  repo_name: string;
  tool_score: number;
  tool_grade: string;
}

interface StaleRepo {
  name: string;
  days: number;
}

interface Report {
  generated_at: string;
  snapshot_time: string;
  total_repos: number;
  grade_distribution: Record<string, number>;
  deltas: Delta[];
  worst_tools_fleet: WorstTool[];
  stale_repos: StaleRepo[];
}

function gradeColor(g: string | null | undefined): string {
  switch (g) {
    case "A": return "text-emerald-400";
    case "B": return "text-blue-400";
    case "C": return "text-amber-400";
    case "D": return "text-orange-400";
    case "F": return "text-red-400";
    default: return "text-zinc-400";
  }
}

function GradeBar({
  label,
  count,
  total,
}: {
  label: string;
  count: number;
  total: number;
}) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  const color =
    label === "A"
      ? "bg-emerald-500"
      : label === "B"
        ? "bg-blue-500"
        : label === "C"
          ? "bg-amber-500"
          : label === "D"
            ? "bg-orange-500"
            : "bg-red-500";
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-4 font-bold text-right">{label}</span>
      <div className="flex-1 bg-zinc-800 rounded-full h-4 overflow-hidden">
        <div
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-right text-zinc-400">{count}</span>
    </div>
  );
}

interface Props {
  onBack: () => void;
}

export default function ReportView({ onBack }: Props) {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const r = await fetch("/api/report");
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        if (!cancelled) setReport(data);
      } catch (e: unknown) {
        if (!cancelled)
          setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (loading)
    return (
      <div className="text-center py-12 text-zinc-400">
        Loading report...
      </div>
    );

  if (error || !report) {
    return (
      <div className="text-center py-12">
        <p className="text-red-400 mb-2">{error || "No report data"}</p>
        <button
          type="button"
          onClick={onBack}
          className="text-blue-400 underline text-sm"
        >
          <ArrowLeft className="w-3.5 h-3.5 inline mr-1" />
          Back
        </button>
      </div>
    );
  }

  const grades = report.grade_distribution || {};
  const total = report.total_repos || 0;
  const deltas = (report.deltas || []).filter(
    (d) => d.score_change !== null && d.score_change !== 0,
  );
  const worstTools = report.worst_tools_fleet || [];
  const stale = report.stale_repos || [];

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
        <h2 className="text-lg font-bold mb-1">Daily Fleet Report</h2>
        <p className="text-xs text-zinc-400">
          Generated: {new Date(report.generated_at).toLocaleString()}
          {report.snapshot_time &&
            ` \u00b7 Snapshot: ${new Date(report.snapshot_time).toLocaleString()}`}
        </p>
      </div>

      {/* Grade Distribution */}
      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5 mb-4">
        <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
          Grade Distribution ({total} repos)
        </h3>
        <div className="space-y-1.5">
          {["A", "B", "C", "D", "F"].map((g) => (
            <GradeBar
              key={g}
              label={g}
              count={grades[g] || 0}
              total={total}
            />
          ))}
          {grades["none"] > 0 && (
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <span className="w-4 font-bold text-right">?</span>
              <span>{grades["none"]} unscored</span>
            </div>
          )}
        </div>
      </div>

      {/* Score Changes */}
      {deltas.length > 0 && (
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5 mb-4">
          <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Score Changes ({deltas.length})
          </h3>
          <div className="space-y-1">
            {deltas
              .sort(
                (a, b) =>
                  Math.abs(b.score_change || 0) -
                  Math.abs(a.score_change || 0),
              )
              .map((d) => {
                const up = (d.score_change || 0) > 0;
                return (
                  <div
                    key={d.repo_name}
                    className="flex items-center gap-3 text-sm"
                  >
                    <span className="font-medium w-40 truncate">
                      {d.repo_name}
                    </span>
                    <span className="text-zinc-400">
                      {d.previous_score != null
                        ? d.previous_score.toFixed(2)
                        : "\u2014"}
                    </span>
                    <span className="text-zinc-400">&rarr;</span>
                    <span className="text-zinc-100">
                      {d.current_score != null
                        ? d.current_score.toFixed(2)
                        : "\u2014"}
                    </span>
                    <span
                      className={`font-medium flex items-center gap-0.5 ${
                        up ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {up ? (
                        <TrendingUp className="w-3.5 h-3.5" />
                      ) : (
                        <TrendingDown className="w-3.5 h-3.5" />
                      )}
                      {Math.abs(d.score_change || 0).toFixed(2)}
                    </span>
                    {d.current_worst_tool && (
                      <span className="text-xs text-zinc-400">
                        worst: {d.current_worst_tool}
                      </span>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Worst Tools */}
      {worstTools.length > 0 && (
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5 mb-4">
          <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-3">
            Worst Tools Fleet-Wide
          </h3>
          <div className="space-y-1">
            {worstTools.map((t, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="text-zinc-400 w-6 text-right">
                  {i + 1}.
                </span>
                <span className="font-mono">{t.tool_name}</span>
                <span className="text-zinc-400">in</span>
                <span className="font-medium">{t.repo_name}</span>
                <span className={gradeColor(t.tool_grade)}>
                  {t.tool_grade}
                </span>
                <span className="text-zinc-400">
                  {t.tool_score?.toFixed(1)}/5
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stale Repos */}
      {stale.length > 0 && (
        <div className="bg-red-900/20 border border-red-800/50 rounded-lg p-5 mb-4">
          <h3 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3">
            Stale Repos (&gt;7 days)
          </h3>
          <p className="text-xs text-red-300/70 mb-2">
            These repos need a release + Sync Server on glama.ai:
          </p>
          <div className="space-y-1">
            {stale.map((s) => (
              <div
                key={s.name}
                className="flex items-center gap-3 text-sm"
              >
                <span className="text-red-300">{s.name}</span>
                <span className="text-red-400/70">
                  {s.days} days stale
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
