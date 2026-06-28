import { useState } from "react";
import {
  BarChart3,
  ChevronLeft,
  ChevronRight,
  HelpCircle,
  LayoutDashboard,
  MessageSquare,
  RefreshCw,
  Server,
  Settings,
  Wrench,
} from "lucide-react";

interface Props {
  activePage: string;
  onNavigate: (page: string) => void;
  onRefresh: () => void;
  refreshing: boolean;
  repoCount: number;
  gradeCounts: Record<string, number>;
}

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "report", label: "Report", icon: BarChart3 },
  { id: "tools", label: "Tools", icon: Wrench },
  { id: "chat", label: "Chat", icon: MessageSquare },
  { id: "help", label: "Help", icon: HelpCircle },
  { id: "settings", label: "Settings", icon: Settings },
];

export function Sidebar({
  activePage,
  onNavigate,
  onRefresh,
  refreshing,
  repoCount,
  gradeCounts,
}: Props) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`${
        collapsed ? "w-16" : "w-56"
      } transition-all duration-200 border-r border-zinc-800 bg-zinc-950 flex flex-col h-screen sticky top-0`}
    >
      {/* Logo */}
      <div className="p-4 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-blue-400 shrink-0" />
          {!collapsed && (
            <span className="font-bold text-sm text-zinc-100">
              Glama Status
            </span>
          )}
        </div>
        {!collapsed && (
          <p className="text-xs text-zinc-400 mt-1">
            {repoCount} repos tracked
          </p>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active =
            activePage === item.id ||
            (item.id === "dashboard" && activePage === "detail");
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                active
                  ? "bg-zinc-800 text-zinc-100"
                  : "text-zinc-400 hover:text-zinc-300 hover:bg-zinc-900"
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Grade summary */}
      {!collapsed && (
        <div className="p-3 border-t border-zinc-800">
          <div className="flex justify-between text-xs">
            <span className="text-emerald-400">A {gradeCounts.A || 0}</span>
            <span className="text-blue-400">B {gradeCounts.B || 0}</span>
            <span className="text-amber-400">C {gradeCounts.C || 0}</span>
            <span className="text-orange-400">D {gradeCounts.D || 0}</span>
            <span className="text-red-400">F {gradeCounts.F || 0}</span>
          </div>
        </div>
      )}

      {/* Refresh + Collapse */}
      <div className="p-2 border-t border-zinc-800 flex items-center gap-1">
        <button
          type="button"
          onClick={onRefresh}
          disabled={refreshing}
          className="flex-1 flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-xs text-zinc-400 hover:text-zinc-300 hover:bg-zinc-900 transition-colors disabled:opacity-50"
          title="Refresh scores"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`}
          />
          {!collapsed && (refreshing ? "Scraping..." : "Refresh")}
        </button>
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          className="p-1.5 rounded text-zinc-400 hover:text-zinc-300 hover:bg-zinc-900 transition-colors shrink-0"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
