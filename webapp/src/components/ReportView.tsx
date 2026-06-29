import { useEffect, useState } from "react";
import {
  ExternalLink,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Trophy,
  Clock,
  ArrowRight,
} from "lucide-react";

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

function gBg(g: string): string {
  switch (g) {
    case "A": return "bg-emerald-500";
    case "B": return "bg-blue-500";
    case "C": return "bg-amber-500";
    case "D": return "bg-orange-500";
    case "F": return "bg-red-500";
    default: return "bg-zinc-600";
  }
}

export default function ReportView() {
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
        if (!cancelled) setReport(await r.json());
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
      <div className="text-center py-20 text-zinc-400">
        <BarChart3 className="w-10 h-10 mx-auto mb-4 text-zinc-600 animate-pulse" />
        Loading report...
      </div>
    );

  if (error || !report)
    return (
      <div className="text-center py-20 text-zinc-400">
        <AlertTriangle className="w-10 h-10 mx-auto mb-4 text-red-400" />
        <p className="text-red-400">{error || "No report data"}</p>
        <p className="text-sm mt-2">Run a refresh first.</p>
      </div>
    );

  const grades = report.grade_distribution || {};
  const total = report.total_repos || 1;
  const deltas = (report.deltas || []).filter(
    (d) => d.score_change !== null && d.score_change !== 0,
  );
  const worstTools = report.worst_tools_fleet || [];
  const stale = report.stale_repos || [];

  const aCount = grades.A || 0;
  const bCount = grades.B || 0;
  const cCount = grades.C || 0;
  const dCount = grades.D || 0;
  const fCount = grades.F || 0;
  const scored = aCount + bCount + cCount + dCount + fCount;

  const avgScore =
    scored > 0
      ? (aCount * 4.25 + bCount * 3.25 + cCount * 2.5 + dCount * 1.5 + fCount * 0.5) / scored
      : 0;

  const healthLabel =
    avgScore >= 3.5 ? "Strong" : avgScore >= 3.0 ? "Good" : avgScore >= 2.0 ? "Needs Work" : "Critical";

  const healthColor =
    avgScore >= 3.5 ? "text-emerald-400" : avgScore >= 3.0 ? "text-blue-400" : avgScore >= 2.0 ? "text-amber-400" : "text-red-400";

  const improved = deltas.filter((d) => (d.score_change || 0) > 0).length;
  const declined = deltas.filter((d) => (d.score_change || 0) < 0).length;

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
          Fleet Report
        </h1>
        <p className="text-sm text-zinc-400 mt-1">
          {report.snapshot_time
            ? `Snapshot: ${new Date(report.snapshot_time).toLocaleString()}`
            : "No snapshot yet"}{" "}
          &middot; Generated: {new Date(report.generated_at).toLocaleString()}
        </p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
          <div className="text-xs text-zinc-400 uppercase tracking-wider mb-1">
            Repos Tracked
          </div>
          <div className="text-2xl font-bold text-zinc-100">{total}</div>
          <div className="text-xs text-zinc-400 mt-0.5">{scored} scored</div>
        </div>
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
          <div className="text-xs text-zinc-400 uppercase tracking-wider mb-1">
            Fleet Health
          </div>
          <div className={`text-2xl font-bold ${healthColor}`}>
            {avgScore.toFixed(1)}
          </div>
          <div className={`text-xs mt-0.5 ${healthColor}`}>{healthLabel}</div>
        </div>
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
          <div className="text-xs text-zinc-400 uppercase tracking-wider mb-1">
            Trends
          </div>
          <div className="flex items-center gap-3 mt-1">
            <span className="flex items-center gap-1 text-emerald-400 text-sm font-medium">
              <TrendingUp className="w-4 h-4" /> {improved}
            </span>
            <span className="flex items-center gap-1 text-red-400 text-sm font-medium">
              <TrendingDown className="w-4 h-4" /> {declined}
            </span>
          </div>
        </div>
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-4">
          <div className="text-xs text-zinc-400 uppercase tracking-wider mb-1">
            Stale
          </div>
          <div className="text-2xl font-bold text-zinc-100">
            {stale.length}
          </div>
          <div className="text-xs text-zinc-400 mt-0.5">
            {stale.length > 0 ? "needs rescan" : "all fresh"}
          </div>
        </div>
      </div>

      {/* Grade Distribution + Trends side by side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Grade Distribution */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Trophy className="w-4 h-4 text-amber-400" />
            <h2 className="font-semibold text-zinc-100">
              Grade Distribution
            </h2>
          </div>
          {/* Stacked bar */}
          <div className="flex h-6 rounded-full overflow-hidden mb-3">
            {["A", "B", "C", "D", "F"].map((g) => {
              const count = grades[g] || 0;
              const pct = (count / total) * 100;
              return pct > 0 ? (
                <div
                  key={g}
                  className={`${gBg(g)} flex items-center justify-center text-xs font-bold text-white`}
                  style={{ width: `${pct}%` }}
                >
                  {pct > 8 ? g : ""}
                </div>
              ) : null;
            })}
          </div>
          {/* Legend */}
          <div className="flex gap-4 text-sm">
            {["A", "B", "C", "D", "F"].map((g) => (
              <div key={g} className="flex items-center gap-1.5">
                <div className={`w-3 h-3 rounded ${gBg(g)}`} />
                <span className={`font-medium ${gradeColor(g)}`}>
                  {grades[g] || 0}
                </span>
                <span className="text-zinc-400 text-xs">{g}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Score Changes */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <h2 className="font-semibold text-zinc-100">
              Score Changes
            </h2>
            {deltas.length > 0 && (
              <span className="text-xs text-zinc-400 ml-auto">
                {deltas.length} repos changed
              </span>
            )}
          </div>
          {deltas.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-auto">
              {deltas
                .sort((a, b) => Math.abs(b.score_change || 0) - Math.abs(a.score_change || 0))
                .slice(0, 8)
                .map((d) => {
                  const up = (d.score_change || 0) > 0;
                  return (
                    <div key={d.repo_name} className="flex items-center gap-2 text-sm">
                      <span className="w-32 truncate text-zinc-300 font-medium">
                        {d.repo_name}
                      </span>
                      <span className="text-zinc-400 text-xs">
                        {d.previous_score?.toFixed(1)}
                      </span>
                      <ArrowRight className="w-3 h-3 text-zinc-500" />
                      <span className="text-zinc-100 text-xs font-medium">
                        {d.current_score?.toFixed(1)}
                      </span>
                      <span
                        className={`flex items-center gap-0.5 text-xs font-bold ml-auto ${
                          up ? "text-emerald-400" : "text-red-400"
                        }`}
                      >
                        {up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        {d.score_change! > 0 ? "+" : ""}
                        {d.score_change?.toFixed(2)}
                      </span>
                    </div>
                  );
                })}
            </div>
          ) : (
            <div className="text-center py-8 text-zinc-400 text-sm">
              <CheckCircle className="w-6 h-6 mx-auto mb-2 text-zinc-500" />
              No changes since last snapshot. Run another refresh to compare.
            </div>
          )}
        </div>
      </div>

      {/* Worst Tools */}
      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <h2 className="font-semibold text-zinc-100">
            Worst Tools Fleet-Wide
          </h2>
          <span className="text-xs text-zinc-400 ml-auto">
            {worstTools.length} tools
          </span>
        </div>
        {worstTools.length > 0 ? (
          <div className="grid gap-2">
            {worstTools.slice(0, 10).map((t, i) => (
              <div
                key={`${t.tool_name}-${t.repo_name}`}
                className="flex items-center gap-3 bg-zinc-950 rounded-lg px-4 py-2.5"
              >
                <span className={`w-6 text-center text-sm font-bold ${gradeColor(t.tool_grade)}`}>
                  {i + 1}
                </span>
                <a
                  href={`https://glama.ai/mcp/tools/${encodeURIComponent(t.tool_name)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-sm text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1"
                >
                  {t.tool_name}
                  <ExternalLink className="w-3 h-3 text-zinc-400" />
                </a>
                <span className="text-zinc-400 text-xs">in</span>
                <span className="text-zinc-300 text-sm font-medium">
                  {t.repo_name}
                </span>
                <div className="ml-auto flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded font-bold ${gBg(t.tool_grade)} text-white`}>
                    {t.tool_grade}
                  </span>
                  <span className="text-zinc-400 text-xs">
                    {t.tool_score?.toFixed(1)}/5
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-zinc-400 text-sm text-center py-4">No tools scored yet.</p>
        )}
      </div>

      {/* Stale Repos */}
      {stale.length > 0 && (
        <div className="bg-red-950/30 border border-red-900/50 rounded-lg p-5">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-4 h-4 text-red-400" />
            <h2 className="font-semibold text-red-300">
              Stale Repos &mdash; No Data in 7+ Days
            </h2>
          </div>
          <p className="text-xs text-red-400/70 mb-3">
            These repos need a new release pushed, then trigger Sync Server on glama.ai.
          </p>
          <div className="flex flex-wrap gap-2">
            {stale.map((s) => (
              <a
                key={s.name}
                href={`https://glama.ai/mcp/servers/${s.name}`}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-red-900/30 border border-red-800/50 rounded-lg px-3 py-1.5 text-sm text-red-300 hover:text-red-200 hover:bg-red-900/50 flex items-center gap-1.5 transition-colors"
              >
                {s.name}
                <span className="text-red-400 text-xs">({s.days}d)</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Action Card */}
      <div className="bg-blue-950/20 border border-blue-900/50 rounded-lg p-5">
        <h2 className="font-semibold text-blue-300 mb-2">What To Do Next</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div className="text-blue-300/80">
            <span className="font-medium">1. Fix the worst tools</span>
            <p className="text-xs text-blue-400/50 mt-0.5">
              Focus on the top 3 tools above. Add Field(description=...) to
              every parameter, add BEHAVIOR sections, add usage guidelines.
            </p>
          </div>
          <div className="text-blue-300/80">
            <span className="font-medium">2. Rescan stale repos</span>
            <p className="text-xs text-blue-400/50 mt-0.5">
              Push a new release for each stale repo, then go to glama.ai
              and trigger Sync Server to get fresh scores.
            </p>
          </div>
          <div className="text-blue-300/80">
            <span className="font-medium">3. Generate fix plans</span>
            <p className="text-xs text-blue-400/50 mt-0.5">
              Run glama_generate_reports() to create per-repo markdown
              fix plans in reports/. Feed them to your IDE LLM.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
