import { useEffect, useState } from "react";
import { Wrench, ExternalLink } from "lucide-react";

interface WorstTool {
  tool_name: string;
  repo_name: string;
  tool_score: number;
  tool_grade: string;
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

export function ToolsPage() {
  const [worstTools, setWorstTools] = useState<WorstTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const r = await fetch("/api/worst-tools?limit=50");
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        if (!cancelled) setWorstTools(Array.isArray(data) ? data : []);
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
        Loading tools...
      </div>
    );

  if (error)
    return (
      <div className="text-center py-12">
        <p className="text-red-400 mb-2">{error}</p>
      </div>
    );

  const byGrade: Record<string, WorstTool[]> = {};
  for (const t of worstTools) {
    const g = t.tool_grade || "?";
    if (!byGrade[g]) byGrade[g] = [];
    byGrade[g].push(t);
  }
  const gradeOrder = ["F", "D", "C", "B", "A"];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
          Tools Overview
        </h1>
        <p className="text-zinc-400 mt-1">
          Fleet-wide tool scores, sorted worst-first. Click a tool name to
          open its Glama detail page.
        </p>
      </div>

      {/* Grade distribution bars */}
      <div className="grid grid-cols-5 gap-3">
        {gradeOrder.map((g) => {
          const count = (byGrade[g] || []).length;
          const total = worstTools.length || 1;
          const pct = (count / total) * 100;
          const colors: Record<string, string> = {
            A: "bg-emerald-500",
            B: "bg-blue-500",
            C: "bg-amber-500",
            D: "bg-orange-500",
            F: "bg-red-500",
          };
          return (
            <div
              key={g}
              className="bg-zinc-900 rounded-lg border border-zinc-800 p-4 text-center"
            >
              <div className={`text-2xl font-bold ${gradeColor(g)}`}>
                {g}
              </div>
              <div className="text-xs text-zinc-400 mt-1">{count} tools</div>
              <div className="mt-2 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${colors[g]}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Tool list grouped by grade */}
      {gradeOrder.map((g) => {
        const tools = byGrade[g] || [];
        if (tools.length === 0) return null;
        return (
          <div key={g}>
            <h3
              className={`text-sm font-semibold uppercase tracking-wider mb-2 ${gradeColor(g)}`}
            >
              Grade {g} ({tools.length})
            </h3>
            <div className="grid gap-1.5">
              {tools.map((t, i) => (
                <div
                  key={`${t.tool_name}-${t.repo_name}-${i}`}
                  className="flex items-center gap-3 bg-zinc-900/50 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm"
                >
                  <span className="text-zinc-400 w-6 text-right text-xs">
                    {i + 1}
                  </span>
                  <a
                    href={`https://glama.ai/tools/${encodeURIComponent(t.tool_name)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-zinc-200 hover:text-blue-400 flex items-center gap-1.5"
                  >
                    {t.tool_name}
                    <ExternalLink className="w-3 h-3 text-zinc-400" />
                  </a>
                  <span className="text-zinc-400">in</span>
                  <span className="text-zinc-400">{t.repo_name}</span>
                  <span className="ml-auto flex items-center gap-2">
                    <span
                      className={`font-bold text-xs ${gradeColor(t.tool_grade)}`}
                    >
                      {t.tool_grade}
                    </span>
                    <span className="text-zinc-400 text-xs">
                      {t.tool_score?.toFixed(1)}/5
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {worstTools.length === 0 && (
        <div className="text-center py-12 text-zinc-400">
          <Wrench className="w-12 h-12 mx-auto mb-4 text-zinc-700" />
          <p>No tools data available.</p>
          <p className="text-sm mt-1">
            Run a refresh to populate the database.
          </p>
        </div>
      )}
    </div>
  );
}
