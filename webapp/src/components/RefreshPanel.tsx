import React, { useState } from "react";

interface Props {
  onRefresh: () => void;
}

export default function RefreshPanel({ onRefresh }: Props) {
  const [refreshing, setRefreshing] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleRefresh = async () => {
    setRefreshing(true);
    setResult(null);
    try {
      const r = await fetch("/api/refresh", { method: "POST" });
      const data = await r.json();
      setResult(data.message || "Refresh complete");
      onRefresh();
    } catch (e: unknown) {
      setResult(e instanceof Error ? e.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={handleRefresh}
        disabled={refreshing}
        className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 text-xs px-3 py-1.5 rounded font-medium transition-colors"
      >
        {refreshing ? "Scraping..." : "Refresh Now"}
      </button>
      {result && (
        <div className="absolute right-0 top-full mt-2 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-xs text-gray-300 whitespace-nowrap z-10 shadow-xl">
          {result}
          <button
            type="button"
            onClick={() => setResult(null)}
            className="ml-2 text-gray-600 hover:text-gray-400"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
