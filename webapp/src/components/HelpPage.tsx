import {
  BookOpen,
  ExternalLink,
  FileText,
  HelpCircle,
  Info,
  RefreshCw,
  Server,
  Shield,
  Terminal,
  TrendingUp,
} from "lucide-react";
import { useState } from "react";

const TABS = [
  { id: "overview", label: "Overview", icon: Info },
  { id: "scoring", label: "Scoring", icon: TrendingUp },
  { id: "tools", label: "MCP Tools", icon: Terminal },
  { id: "api", label: "REST API", icon: Server },
  { id: "faq", label: "FAQ", icon: HelpCircle },
];

export function HelpPage() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
          Help & Documentation
        </h1>
        <p className="text-zinc-400 mt-1">
          Glama score tracking for the sandraschi fleet -- scrape, store,
          report
        </p>
      </div>

      {/* Horizontal Tabs */}
      <div className="flex flex-wrap gap-1 rounded-lg bg-zinc-900 p-1 border border-zinc-800 w-fit">
        {TABS.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-all ${
                activeTab === t.id
                  ? "bg-zinc-950 text-zinc-100 shadow-sm ring-1 ring-zinc-800"
                  : "text-zinc-400 hover:text-zinc-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && <OverviewTab />}
      {activeTab === "scoring" && <ScoringTab />}
      {activeTab === "tools" && <ToolsTab />}
      {activeTab === "api" && <ApiTab />}
      {activeTab === "faq" && <FaqTab />}
    </div>
  );
}

function OverviewTab() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold text-zinc-100">What It Does</h3>
        </div>
        <div className="text-sm text-zinc-400 space-y-2">
          <p>
            glama-status-mcp scrapes the{" "}
            <a
              href="https://glama.ai/mcp/servers"
              className="text-blue-400 underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Glama MCP server registry
            </a>{" "}
            daily for TDQS (Tool Definition Quality Score) grades across the
            sandraschi fleet.
          </p>
          <ul className="list-disc list-inside text-xs space-y-1">
            <li>
              <strong>10 repos</strong> tracked (out of 35 registered on Glama)
            </li>
            <li>Per-tool scores across 6 TDQS dimensions</li>
            <li>Snapshot history with delta tracking</li>
            <li>Staleness detection (&gt;7 days since last scrape)</li>
            <li>Daily markdown report generation</li>
          </ul>
        </div>
      </div>

      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <div className="flex items-center gap-2 mb-3">
          <RefreshCw className="w-5 h-5 text-emerald-400" />
          <h3 className="font-semibold text-zinc-100">How It Works</h3>
        </div>
        <div className="text-sm text-zinc-400 space-y-2">
          <p>Four-step pipeline that runs daily:</p>
          <ol className="list-decimal list-inside text-xs space-y-1">
            <li>
              <strong>Scrape</strong> -- fetch score pages from glama.ai
            </li>
            <li>
              <strong>Parse</strong> -- extract grades, dimensions, tool scores
            </li>
            <li>
              <strong>Store</strong> -- SQLite with snapshot history
            </li>
            <li>
              <strong>Report</strong> -- grade distribution, deltas, stale repos
            </li>
          </ol>
          <p className="text-xs mt-2 text-zinc-400">
            Polite scraping: 1s delay between requests, descriptive user agent.
            BrightData proxy fallback via{" "}
            <code className="text-zinc-400">GLAMA_USE_BRIGHTDATA=1</code>.
          </p>
        </div>
      </div>

      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Server className="w-5 h-5 text-amber-400" />
          <h3 className="font-semibold text-zinc-100">Architecture</h3>
        </div>
        <div className="text-xs text-zinc-400 font-mono space-y-1">
          <p>
            src/glama_status_mcp/
            <span className="text-zinc-400">server.py</span>{" "}
            <span className="text-zinc-400">FastMCP + FastAPI</span>
          </p>
          <p>
            src/glama_status_mcp/
            <span className="text-zinc-400">scraper.py</span>{" "}
            <span className="text-zinc-400">HTML scraper</span>
          </p>
          <p>
            src/glama_status_mcp/
            <span className="text-zinc-400">database.py</span>{" "}
            <span className="text-zinc-400">SQLite + deltas</span>
          </p>
          <p>
            webapp/{" "}
            <span className="text-zinc-400">Vite + React + Tailwind v4</span>
          </p>
          <p>
            tests/ <span className="text-zinc-400">35 tests (pytest)</span>
          </p>
          <p>
            webapp/e2e/{" "}
            <span className="text-zinc-400">Playwright E2E</span>
          </p>
        </div>
      </div>

      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Terminal className="w-5 h-5 text-purple-400" />
          <h3 className="font-semibold text-zinc-100">Quick Start</h3>
        </div>
        <div className="text-xs text-zinc-400 space-y-2">
          <pre className="bg-zinc-950 rounded p-3 text-zinc-300 text-xs overflow-x-auto">
{`# Full stack (backend + frontend + browser)
.\\start.ps1

# Backend only
.\\start.ps1 -BackendOnly

# Via just recipe
just install
just web          # HTTP mode on :11072
just web-frontend # Vite dev on :11073
just refresh      # Manual scrape + snapshot`}
          </pre>
        </div>
      </div>
    </div>
  );
}

function ScoringTab() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <h3 className="font-semibold text-zinc-100 mb-3">
          TDQS Formula (Glama)
        </h3>
        <div className="text-sm text-zinc-400 space-y-3">
          <div className="bg-zinc-950 rounded p-3 text-center">
            <span className="text-xl font-mono font-bold text-zinc-100">
              Score = 0.6 x mean + 0.4 x minimum
            </span>
          </div>
          <p className="text-xs text-zinc-400">
            One bad tool pulls the entire server down. Fix the worst tool first.
          </p>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400">
                <th className="text-left py-1.5">Grade</th>
                <th className="text-right py-1.5">Threshold</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="py-1 text-emerald-400">A</td>
                <td className="py-1 text-right">&ge; 3.5</td>
              </tr>
              <tr>
                <td className="py-1 text-blue-400">B</td>
                <td className="py-1 text-right">&ge; 3.0</td>
              </tr>
              <tr>
                <td className="py-1 text-amber-400">C</td>
                <td className="py-1 text-right">&ge; 2.0</td>
              </tr>
              <tr>
                <td className="py-1 text-orange-400">D</td>
                <td className="py-1 text-right">&ge; 1.0</td>
              </tr>
              <tr>
                <td className="py-1 text-red-400">F</td>
                <td className="py-1 text-right">&lt; 1.0</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <h3 className="font-semibold text-zinc-100 mb-3">
          6 TDQS Dimensions
        </h3>
        <div className="text-sm text-zinc-400 space-y-2">
          {[
            ["Purpose Clarity", "25%", "First sentence states what the tool does"],
            ["Usage Guidelines", "20%", "When to / not to call, preconditions"],
            ["Behavioral Transparency", "20%", "Returns, side effects, errors"],
            ["Parameter Semantics", "15%", "Every param: type, values, effect"],
            ["Conciseness & Structure", "10%", "Not a wall of text, not one line"],
            ["Contextual Completeness", "10%", "Enough to use without source code"],
          ].map(([dim, weight, desc]) => (
            <div key={dim} className="flex items-start gap-2">
              <span className="text-xs font-mono text-blue-400 w-8 mt-0.5">
                {weight}
              </span>
              <div>
                <span className="text-zinc-200">{dim}</span>
                <p className="text-xs text-zinc-400">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5 md:col-span-2">
        <h3 className="font-semibold text-zinc-100 mb-3">
          Server Coherence Dimensions
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          {[
            ["Disambiguation", "Unique tool names without collision"],
            ["Naming Consistency", "Verb-led snake_case across all tools"],
            ["Tool Count", "Appropriate count (not too many, not too few)"],
            ["Completeness", "Covers advertised scope without gaps"],
          ].map(([label, desc]) => (
            <div
              key={label}
              className="bg-zinc-950 rounded p-3"
            >
              <p className="text-zinc-200 font-medium text-xs">{label}</p>
              <p className="text-xs text-zinc-400 mt-1">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ToolsTab() {
  return (
    <div className="space-y-4">
      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <h3 className="font-semibold text-zinc-100 mb-3">
          MCP Tools Reference
        </h3>
        <div className="text-sm text-zinc-400 space-y-4">
          {[
            {
              name: "glama_status",
              desc: "Portmanteau: list, get, worst_tools, refresh, history, staleness, report, deltas",
              ops: [
                "list -- All repos, worst-first",
                "get -- Per-tool breakdown (repo_name required)",
                "worst_tools -- Lowest-scoring tools fleet-wide",
                "refresh -- Rescrape all repos + snapshot",
                "history -- Recent refresh log entries",
                "staleness -- Repos >7d since last scrape",
                "report -- Full daily status report",
                "deltas -- Score changes since last snapshot",
              ],
            },
            {
              name: "glama_scores_summary",
              desc: "Compact fleet-wide score summary with grade distribution",
              ops: [],
            },
            {
              name: "glama_daily_report",
              desc: "Full markdown report: grade table, score deltas, worst tools, stale repos",
              ops: [],
            },
            {
              name: "show_glama_status_card",
              desc: "Prefab UI card -- fleet overview dashboard",
              ops: [],
            },
            {
              name: "show_glama_repo_card",
              desc: "Prefab UI card -- per-repo score breakdown with tool list",
              ops: [],
            },
          ].map((tool) => (
            <div key={tool.name}>
              <h4 className="font-mono text-zinc-200 text-sm">
                {tool.name}()
              </h4>
              <p className="text-xs text-zinc-400 mt-0.5 mb-1">
                {tool.desc}
              </p>
              {tool.ops.length > 0 && (
                <ul className="list-disc list-inside text-xs text-zinc-400 space-y-0.5 ml-2">
                  {tool.ops.map((op) => (
                    <li key={op}>
                      <span className="text-zinc-400">{op}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <h3 className="font-semibold text-zinc-100 mb-3">
          Claude Desktop Registration
        </h3>
        <pre className="bg-zinc-950 rounded p-3 text-zinc-300 text-xs overflow-x-auto">
{`{
  "mcpServers": {
    "glama-status": {
      "command": "uv",
      "args": [
        "--directory", "D:\\\\Dev\\\\repos\\\\glama-status-mcp",
        "run", "glama-status-mcp"
      ]
    }
  }
}`}
        </pre>
        <p className="text-xs text-zinc-400 mt-2">
          Config file:{" "}
          <code className="text-zinc-400">
            %APPDATA%\Claude\claude_desktop_config.json
          </code>
        </p>
      </div>
    </div>
  );
}

function ApiTab() {
  return (
    <div className="space-y-4">
      <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-5">
        <h3 className="font-semibold text-zinc-100 mb-3">REST API</h3>
        <p className="text-xs text-zinc-400 mb-3">
          All endpoints are at{" "}
          <code className="text-zinc-400">http://127.0.0.1:11072</code>
        </p>
        <div className="space-y-3">
          {[
            ["GET", "/health", "Server health check"],
            ["GET", "/api/repos", "All repos with per-tool breakdowns"],
            ["GET", "/api/repos/{name}", "Single repo tool breakdown"],
            ["GET", "/api/worst-tools?limit=20", "Lowest-scoring tools fleet-wide"],
            ["POST", "/api/refresh", "Trigger rescrape + snapshot"],
            ["GET", "/api/history?limit=10", "Recent refresh log entries"],
            ["GET", "/api/report", "Full daily report"],
            ["GET", "/api/deltas", "Score changes since last snapshot"],
            ["POST", "/mcp", "MCP HTTP transport (JSON-RPC)"],
          ].map(([method, path, desc]) => (
            <div
              key={path}
              className="flex items-start gap-3 text-sm"
            >
              <span
                className={`font-mono text-xs px-2 py-0.5 rounded ${
                  method === "GET"
                    ? "bg-emerald-900/50 text-emerald-400"
                    : "bg-blue-900/50 text-blue-400"
                }`}
              >
                {method}
              </span>
              <code className="text-zinc-300 text-xs">{path}</code>
              <span className="text-zinc-400 text-xs ml-auto">{desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FaqTab() {
  return (
    <div className="space-y-3">
      {[
        {
          q: "How often are scores refreshed?",
          a: "A Windows Scheduled Task runs daily at 6:00 AM. You can also trigger a manual refresh via the Refresh Now button in the dashboard, or call glama_status(operation='refresh').",
        },
        {
          q: "Why does the dashboard show 'no scores'?",
          a: "Run a refresh first. The database starts empty. Click Refresh Now or run just refresh to scrape Glama and populate the database.",
        },
        {
          q: "How is the overall score calculated?",
          a: "Glama uses the TDQS formula: 60% weighted mean + 40% minimum across all tools. One low-scoring tool pulls the entire server grade down -- fix the worst tool first.",
        },
        {
          q: "What does 'stale' mean?",
          a: "A repo is stale if its last scrape was more than 7 days ago. This means the repo needs a new release pushed to Glama and a Sync Server triggered on glama.ai.",
        },
        {
          q: "Why do only 10 repos have scores?",
          a: "Out of ~35 sandraschi repos registered on Glama, only 10 have been analyzed (submitted and processed by the Glama scoring pipeline). The remaining 25 have pages but no tool scores yet.",
        },
        {
          q: "Can I add more repos to track?",
          a: "Call glama_status(operation='discover') to auto-find all repos for your Glama author. Or add them individually with glama_status(operation='add_repo', repo_name='my-repo'). Edit config/fleet-repos.json to manage them manually.",
        },
        {
          q: "What ports does the server use?",
          a: "Backend: 11072 (FastAPI + MCP HTTP /mcp). Frontend: 11073 (Vite dev server). See mcp-central-docs/operations/WEBAPP_PORTS.md.",
        },
        {
          q: "How do I improve a repo's score?",
          a: "Use the MCP prompt glama_improvement_plan(repo_name) to get a per-tool priority list. Focus on: adding Field(description=...) to params, behavioral warnings for destructive ops, and 'When to use/not to use' guidance.",
        },
      ].map(({ q, a }) => (
        <div
          key={q}
          className="bg-zinc-900 rounded-lg border border-zinc-800 p-4"
        >
          <h4 className="font-medium text-zinc-200 text-sm mb-1">{q}</h4>
          <p className="text-xs text-zinc-400 leading-relaxed">{a}</p>
        </div>
      ))}
    </div>
  );
}
