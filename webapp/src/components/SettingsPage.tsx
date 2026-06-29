import { useState, useEffect } from "react";
import { ExternalLink, Settings as SettingsIcon, Sparkles } from "lucide-react";

const STORAGE_KEY = "glama-status-gh-account";

interface LlmSettings {
  provider: string;
  model: string;
  base_url: string;
  api_key: string;
}

export function SettingsPage() {
  const [account, setAccount] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || "sandraschi";
    } catch {
      return "sandraschi";
    }
  });
  const [saved, setSaved] = useState(false);
  const [llm, setLlm] = useState<LlmSettings>({
    provider: "ollama",
    model: "",
    base_url: "http://127.0.0.1:11434/v1",
    api_key: "",
  });
  const [llmSaved, setLlmSaved] = useState(false);
  const [llmLoading, setLlmLoading] = useState(true);

  useEffect(() => {
    if (saved) {
      const t = setTimeout(() => setSaved(false), 2000);
      return () => clearTimeout(t);
    }
  }, [saved]);

  useEffect(() => {
    if (llmSaved) {
      const t = setTimeout(() => setLlmSaved(false), 2000);
      return () => clearTimeout(t);
    }
  }, [llmSaved]);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch("/api/settings/llm");
        if (r.ok) setLlm(await r.json());
      } catch {
        /* use defaults */
      } finally {
        setLlmLoading(false);
      }
    })();
  }, []);

  const handleSaveAccount = () => {
    try {
      localStorage.setItem(STORAGE_KEY, account);
      setSaved(true);
    } catch {
      /* localStorage unavailable */
    }
  };

  const handleSaveLlm = async () => {
    try {
      const r = await fetch("/api/settings/llm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(llm),
      });
      if (r.ok) setLlmSaved(true);
    } catch {
      /* backend offline */
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100">
          Settings
        </h1>
        <p className="text-zinc-400 mt-1 text-sm">
          Configure the Glama tracker preferences.
        </p>
      </div>

      {/* Glama Account */}
      <div className="bg-zinc-900 rounded-lg border border-zinc-700 p-5 space-y-4">
        <div className="flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-zinc-400" />
          <h2 className="font-semibold text-zinc-100">
            Glama / GitHub Account
          </h2>
        </div>
        <p className="text-sm text-zinc-400">
          The author namespace used for Glama score page URLs.
        </p>
        <div className="flex gap-3">
          <input
            type="text"
            value={account}
            onChange={(e) => setAccount(e.target.value)}
            placeholder="sandraschi"
            className="flex-1 bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-blue-500"
          />
          <button
            type="button"
            onClick={handleSaveAccount}
            className="bg-blue-600 hover:bg-blue-500 text-white text-sm px-4 py-2 rounded-md font-medium transition-colors"
          >
            {saved ? "Saved" : "Save"}
          </button>
        </div>
        <div className="text-xs text-zinc-400">
          Score URLs: <code className="text-zinc-300">glama.ai/mcp/servers/{account || "sandraschi"}/{"{repo}"}/score</code>
          <br />
          <a
            href={`https://glama.ai/mcp/servers?query=author%3A${account || "sandraschi"}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 mt-1"
          >
            View on Glama <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* LLM Provider */}
      <div className="bg-zinc-900 rounded-lg border border-zinc-700 p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-400" />
          <h2 className="font-semibold text-zinc-100">
            LLM Provider
          </h2>
        </div>
        <p className="text-sm text-zinc-400">
          Used by <code className="text-zinc-300">glama_agentic_analyze</code> and report generation when
          MCP sampling is unavailable. Also used by the Chat page.
        </p>

        {llmLoading ? (
          <p className="text-sm text-zinc-500">Loading...</p>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-zinc-400 uppercase tracking-wider">
                  Provider
                </label>
                <select
                  value={llm.provider}
                  onChange={(e) =>
                    setLlm({ ...llm, provider: e.target.value })
                  }
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-200 mt-1"
                >
                  <option value="ollama">Ollama</option>
                  <option value="lmstudio">LM Studio</option>
                  <option value="openai">OpenAI-compatible</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-zinc-400 uppercase tracking-wider">
                  Model
                </label>
                <input
                  type="text"
                  value={llm.model}
                  onChange={(e) =>
                    setLlm({ ...llm, model: e.target.value })
                  }
                  placeholder="llama3.2:3b"
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-200 mt-1 placeholder:text-zinc-500"
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-zinc-400 uppercase tracking-wider">
                Base URL
              </label>
              <input
                type="text"
                value={llm.base_url}
                onChange={(e) =>
                  setLlm({ ...llm, base_url: e.target.value })
                }
                className="w-full bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-200 mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-zinc-400 uppercase tracking-wider">
                API Key (optional, for cloud providers)
              </label>
              <input
                type="password"
                value={llm.api_key}
                onChange={(e) =>
                  setLlm({ ...llm, api_key: e.target.value })
                }
                placeholder="sk-..."
                className="w-full bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-200 mt-1 placeholder:text-zinc-500"
              />
            </div>
            <div className="flex justify-between items-center">
              <div className="text-xs text-zinc-400">
                Detection: Ollama on port 11434, LM Studio on 1234
              </div>
              <button
                type="button"
                onClick={handleSaveLlm}
                className="bg-blue-600 hover:bg-blue-500 text-white text-sm px-4 py-2 rounded-md font-medium transition-colors"
              >
                {llmSaved ? "Saved" : "Save"}
              </button>
            </div>
          </>
        )}
      </div>

      {/* About */}
      <div className="bg-zinc-900 rounded-lg border border-zinc-700 p-5">
        <h2 className="font-semibold text-zinc-100 mb-2">About</h2>
        <div className="text-sm text-zinc-400 space-y-1">
          <p>glama-status-mcp v0.1.1</p>
          <p>
            <a
              href="https://github.com/sandraschi/glama-status-mcp"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-1"
            >
              github.com/sandraschi/glama-status-mcp
              <ExternalLink className="w-3 h-3" />
            </a>
          </p>
          <p className="text-zinc-400 mt-2">
            Ports: backend 11072, frontend 11073, MCP /mcp
          </p>
        </div>
      </div>
    </div>
  );
}
