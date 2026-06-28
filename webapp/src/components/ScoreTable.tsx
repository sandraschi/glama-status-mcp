import React, { useMemo, useState } from "react";

interface Tool {
  name: string;
  grade: string;
  score: number;
}

interface Repo {
  name: string;
  overall_grade: string;
  overall_score: number;
  tdqs_grade: string;
  tdqs_mean: number;
  tdqs_min: number;
  coherence_grade: string;
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
          (r.overall_grade || "").toLowerCase().includes(f)
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

  const sortArrow = (key: SortKey) =>
    sortKey === key ? (sortDir === "asc" ? " ▲" : " ▼") : "";

  return (
    <div>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Filter by name or grade..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-500 uppercase text-xs tracking-wider">
              <th
                className="text-left py-3 px-2 cursor-pointer hover:text-gray-300"
                onClick={() => toggleSort("name")}
              >
                Repo{sortArrow("name")}
              </th>
              <th
                className="text-center py-3 px-2 cursor-pointer hover:text-gray-300"
                onClick={() => toggleSort("grade")}
              >
                Grade{sortArrow("grade")}
              </th>
              <th
                className="text-center py-3 px-2 cursor-pointer hover:text-gray-300"
                onClick={() => toggleSort("score")}
              >
                Score{sortArrow("score")}
              </th>
              <th className="text-center py-3 px-2">TDQS μ</th>
              <th className="text-center py-3 px-2">TDQS min</th>
              <th className="text-center py-3 px-2">Coherence</th>
              <th className="text-center py-3 px-2">Maintenance</th>
              <th
                className="text-center py-3 px-2 cursor-pointer hover:text-gray-300"
                onClick={() => toggleSort("tools")}
              >
                Tools{sortArrow("tools")}
              </th>
              <th className="text-center py-3 px-2">Profile</th>
              <th className="text-center py-3 px-2">Release</th>
              <th
                className="text-center py-3 px-2 cursor-pointer hover:text-gray-300"
                onClick={() => toggleSort("stale")}
              >
                Stale{sortArrow("stale")}
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((repo) => {
              const stale = repo.last_scraped ? daysSince(repo.last_scraped) : -1;
              const worstTool = repo.tools?.length
                ? repo.tools.reduce((a, b) => (a.score < b.score ? a : b))
                : null;
              return (
                <tr
                  key={repo.name}
                  className="border-b border-gray-800/50 hover:bg-gray-900/50 cursor-pointer"
                  onClick={() => onSelectRepo(repo.name)}
                >
                  <td className="py-3 px-2 font-medium">{repo.name}</td>
                  <td className={`py-3 px-2 text-center font-bold ${gradeColor(repo.overall_grade)}`}>
                    {repo.overall_grade || " - "}
                  </td>
                  <td className="py-3 px-2 text-center">
                    {repo.overall_score != null ? repo.overall_score.toFixed(2) : " - "}
                  </td>
                  <td className="py-3 px-2 text-center text-gray-400">
                    {repo.tdqs_mean != null ? repo.tdqs_mean.toFixed(2) : " - "}
                  </td>
                  <td className="py-3 px-2 text-center text-gray-400">
                    {repo.tdqs_min != null ? repo.tdqs_min.toFixed(2) : " - "}
                  </td>
                  <td className={`py-3 px-2 text-center ${gradeColor(repo.coherence_grade)}`}>
                    {repo.coherence_grade || " - "}
                  </td>
                  <td className={`py-3 px-2 text-center ${gradeColor(repo.maintenance_grade)}`}>
                    {repo.maintenance_grade || " - "}
                  </td>
                  <td className="py-3 px-2 text-center text-gray-400">
                    {repo.tools?.length || 0}
                    {worstTool && (
                      <span className="text-xs ml-1 text-gray-600">
                        (worst: {worstTool.score.toFixed(1)})
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-2 text-center">
                    <div className="flex items-center gap-1 justify-center">
                      <div className="w-12 bg-gray-800 rounded-full h-1.5">
                        <div
                          className="h-1.5 rounded-full bg-blue-500"
                          style={{ width: `${repo.profile_completion || 0}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">
                        {repo.profile_completion || 0}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-2 text-center text-xs text-gray-500">
                    {repo.latest_release || " - "}
                  </td>
                  <td className="py-3 px-2 text-center">
                    {stale >= 0 ? (
                      <span className={stale > 7 ? "text-red-400" : stale > 3 ? "text-amber-400" : "text-gray-500"}>
                        {stale}d
                      </span>
                    ) : (
                      <span className="text-gray-600"> - </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-gray-600 mt-3">
        {sorted.length} repo{sorted.length !== 1 ? "s" : ""} &middot;
        Click a row for per-tool breakdown &middot;
        Sort by clicking column headers
      </p>
    </div>
  );
}
