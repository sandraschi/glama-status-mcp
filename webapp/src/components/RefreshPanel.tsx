import React from "react";
import { RefreshCw, Loader2 } from "lucide-react";

interface Props {
  onRefresh: () => void;
}

export default function RefreshPanel({ onRefresh }: Props) {
  const [refreshing, setRefreshing] = React.useState(false);
  const [result, setResult] = React.useState<string | null>(null);

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
        className="bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 disabled:text-zinc-400 text-xs px-3 py-1.5 rounded font-medium transition-colors flex items-center gap-1.5"
      >
        {refreshing ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <RefreshCw className="w-3.5 h-3.5" />
        )}
        {refreshing ? "Scraping..." : "Refresh Now"}
      </button>
      {result && (
        <div className="absolute right-0 top-full mt-2 bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-xs text-zinc-300 whitespace-nowrap z-10 shadow-xl">
          {result}
          <button
            type="button"
            onClick={() => setResult(null)}
            className="ml-2 text-zinc-400 hover:text-zinc-400"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
