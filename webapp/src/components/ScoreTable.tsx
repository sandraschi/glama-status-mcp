import React, { useMemo, useState } from "react";
import { ArrowUp, ArrowDown, ArrowUpDown, ExternalLink, Search } from "lucide-react";
import type { Repo, Tool } from "../types";

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

function daysSince(iso: string): number {
  const d = new Date(iso);
  return Math.floor((Date.now() - d.getTime()) / 86400000);
}

interface Props {
  repos: Repo[];
  onSelectRepo: (name: string) => void;
}

type SortKey = "score" | "name" | "grade" | "tools" | "stale";

export default function ScoreTable({ repos, onSelectRepo }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [filter, setFilter] = useState("");

  const sorted = useMemo(() => {
    const list = [...repos];
    if (filter) {
      const f = filter.toLowerCase();
      return list.filter(
        (r) =>
          r.name.toLowerCase().includes(f) ||
          (r.overall_grade || "").toLowerCase().includes(f),
      );
    }
    list.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "score":
          cmp = (a.overall_score || 999) - (b.overall_score || 999);
          break;
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "grade":
          cmp = (a.overall_grade || "Z").localeCompare(b.overall_grade || "Z");
          break;
        case "tools":
          cmp = (a.tools?.length || 0) - (b.tools?.length || 0);
          break;
        case "stale":
          cmp = daysSince(a.last_scraped || "") - daysSince(b.last_scraped || "");
          break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return list;
  }, [repos, sortKey, sortDir, filter]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const sortIcon = (key: SortKey) => {
    if (sortKey !== key) return <ArrowUpDown className="w-3 h-3 inline ml-0.5 opacity-40" />;
    return sortDir === "asc"
      ? <ArrowUp className="w-3 h-3 inline ml-0.5" />
      : <ArrowDown className="w-3 h-3 inline ml-0.5" />;
  };

  return (
    <div>
      <div className="mb-4 relative">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
        <input
          type="text"
          placeholder="Filter by name or grade..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full bg-zinc-900 border border-zinc-700 rounded pl-10 pr-3 py-2 text-sm focus:outline-none focus:border-blue-500 text-zinc-100 placeholder-zinc-600"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-400 uppercase text-xs tracking-wider">
              {(
                [
                  ["name", "left", "Repo"],
                  ["grade", "center", "Grade"],
                  ["score", "center", "Score"],
                  [null, "center", "TDQS μ"],
                  [null, "center", "TDQS min"],
                  [null, "center", "Coh"],
                  [null, "center", "Maint"],
                  ["tools", "center", "Tools"],
                  [null, "center", "Profile"],
                  [null, "center", "Release"],
                  ["stale", "center", "Stale"],
                ] as [SortKey | null, string, string][]
              ).map(([key, align, label]) => (
                <th
                  key={label}
                  className={`py-3 px-2 text-${align} ${
                    key ? "cursor-pointer hover:text-zinc-300" : ""
                  }`}
                  onClick={() => key && toggleSort(key)}
                >
                  {label}
                  {key && sortIcon(key)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((repo) => {
              const stale = repo.last_scraped
                ? daysSince(repo.last_scraped)
                : -1;
              const worstTool = repo.tools?.length
                ? repo.tools.reduce((a, b) =>
                    a.score < b.score ? a : b,
                  )
                : null;
              return (
                <tr
                  key={repo.name}
                  className="border-b border-zinc-800/50 hover:bg-zinc-900/50 cursor-pointer"
                  onClick={() => onSelectRepo(repo.name)}
                >
                  <td className="py-3 px-2">
                    <div className="flex items-center gap-1.5">
                      <span
                        className="font-medium cursor-pointer hover:text-blue-400"
                        onClick={() => onSelectRepo(repo.name)}
                      >
                        {repo.name}
                      </span>
                      <a
                        href={`https://glama.ai/mcp/servers/${ghAccount()}/${repo.name}/score`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-zinc-400 hover:text-blue-400"
                        title="Open Glama score page"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  </td>
                  <td
                    className={`py-3 px-2 text-center font-bold ${gradeColor(repo.overall_grade)}`}
                  >
                    {repo.overall_grade || "\u2014"}
                  </td>
                  <td className="py-3 px-2 text-center">
                    {repo.overall_score != null
                      ? repo.overall_score.toFixed(2)
                      : "\u2014"}
                  </td>
                  <td className="py-3 px-2 text-center text-zinc-400">
                    {repo.tdqs_mean != null
                      ? repo.tdqs_mean.toFixed(2)
                      : "\u2014"}
                  </td>
                  <td className="py-3 px-2 text-center text-zinc-400">
                    {repo.tdqs_min != null
                      ? repo.tdqs_min.toFixed(2)
                      : "\u2014"}
                  </td>
                  <td className={`py-3 px-2 text-center ${gradeColor(repo.coherence_grade)}`}>
                    {repo.coherence_grade || "\u2014"}
                  </td>
                  <td className={`py-3 px-2 text-center ${gradeColor(repo.maintenance_grade)}`}>
                    {repo.maintenance_grade || "\u2014"}
                  </td>
                  <td className="py-3 px-2 text-center text-zinc-400">
                    {repo.tools?.length || 0}
                    {worstTool && (
                      <span className="text-xs ml-1 text-zinc-400">
                        (worst: {worstTool.score.toFixed(1)})
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-2 text-center">
                    <div className="flex items-center gap-1 justify-center">
                      <div className="w-12 bg-zinc-800 rounded-full h-1.5">
                        <div
                          className="h-1.5 rounded-full bg-blue-500"
                          style={{
                            width: `${repo.profile_completion || 0}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs text-zinc-400">
                        {repo.profile_completion || 0}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-center text-xs text-zinc-400">
                    {repo.latest_release || "\u2014"}
                  </td>
                  <td className="py-3 px-2 text-center">
                    {stale >= 0 ? (
                      <span
                        className={
                          stale > 7
                            ? "text-red-400"
                            : stale > 3
                              ? "text-amber-400"
                              : "text-zinc-400"
                        }
                      >
                        {stale}d
                      </span>
                    ) : (
                      <span className="text-zinc-400">\u2014</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-zinc-400 mt-3">
        {sorted.length} repo{sorted.length !== 1 ? "s" : ""} &middot;
        Click a row for per-tool breakdown &middot;
        Sort by clicking column headers
      </p>
    </div>
  );
}
