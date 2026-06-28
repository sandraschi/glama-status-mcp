import { useState, useEffect, useRef, useCallback } from "react";
import { Send, User, Bot, Trash2, Download, Sparkles } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Provider {
  name: string;
  base_url: string;
  available: boolean;
  models: string[];
}

const PERSONALITIES = [
  {
    id: "glama-analyst",
    label: "Glama Analyst",
    prompt: "You are a Glama TDQS score analyst. Analyze tool docstring scores, identify patterns, suggest concrete fixes. Be specific and actionable.",
  },
  {
    id: "sre",
    label: "SRE Engineer",
    prompt: "You are an SRE-focused engineer. Analyze fleet health like production systems. Identify risks, suggest mitigations, prioritize by impact.",
  },
  {
    id: "friendly",
    label: "Friendly Guide",
    prompt: "You are a friendly guide helping improve MCP server docstrings. Explain concepts clearly, encourage good practices, be supportive.",
  },
  {
    id: "short",
    label: "Short & Punchy",
    prompt: "Be extremely concise. Give direct, actionable answers in minimal words. No preamble.",
  },
];

const EXAMPLE_PROMPTS = [
  "Analyze blender-mcp scores and give me 3 fixes",
  "What common docstring problems do you see across the fleet?",
  "How can I improve virtualization-mcp?",
  "Compare email-mcp and steam-mcp scores",
  "Which repo needs the most urgent attention?",
  "What does the TDQS formula mean?",
];

const STORAGE_KEY = "glama-status-chat-history";

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState("ollama");
  const [selectedModel, setSelectedModel] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [personality, setPersonality] = useState(PERSONALITIES[0].id);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch("/api/llm/providers");
        const data = await r.json();
        const p: Provider[] = data.providers || [];
        setProviders(p);
        const avail = p.find((x) => x.available);
        if (avail) {
          setSelectedProvider(avail.name);
          setSelectedModel(avail.models[0] || "");
        }
      } catch {
        /* offline */
      }
    })();
  }, []);

  const currentProvider = providers.find(
    (p) => p.name === selectedProvider,
  );

  const activePrompt =
    PERSONALITIES.find((p) => p.id === personality)?.prompt || "";

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setError(null);
    setSending(true);

    const userMsg: Message = { role: "user", content: text };
    const updated = [...messages, userMsg];
    setMessages(updated);

    try {
      const baseUrl =
        currentProvider?.base_url ||
        `http://127.0.0.1:${selectedProvider === "lmstudio" ? 1234 : 11434}/v1`;
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          provider: selectedProvider,
          model: selectedModel,
          base_url: baseUrl,
          system_prompt: activePrompt,
          api_key: apiKey,
          context: { history: updated.slice(0, -1) },
        }),
      });
      const data = await r.json();
      if (!data.success) throw new Error(data.error || "Chat failed");
      const assistantMsg: Message = {
        role: "assistant",
        content: data.reply,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Chat failed");
    } finally {
      setSending(false);
    }
  }, [input, sending, messages, selectedProvider, selectedModel, currentProvider, activePrompt, apiKey]);

  const handleClear = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const handleExport = () => {
    const text = messages
      .map(
        (m) =>
          `[${m.role === "user" ? "You" : "Assistant"}] ${m.content}`,
      )
      .join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "glama-chat-export.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Side panel: settings */}
      <div className="w-64 shrink-0 space-y-3 overflow-auto">
        <div>
          <label className="text-xs text-zinc-400 uppercase tracking-wider">
            Provider
          </label>
          <select
            value={selectedProvider}
            onChange={(e) => {
              setSelectedProvider(e.target.value);
              const p = providers.find((x) => x.name === e.target.value);
              setSelectedModel(p?.models[0] || "");
            }}
            className="w-full bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-200 mt-1"
          >
            {providers.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name} {p.available ? "" : "(offline)"}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs text-zinc-400 uppercase tracking-wider">
            Model
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-200 mt-1"
          >
            {(currentProvider?.models || []).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
            {(!currentProvider?.models || currentProvider.models.length === 0) && (
              <option value={selectedModel}>{selectedModel || "auto"}</option>
            )}
          </select>
        </div>

        <div>
          <label className="text-xs text-zinc-400 uppercase tracking-wider">
            Personality
          </label>
          <select
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-200 mt-1"
          >
            {PERSONALITIES.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        {selectedProvider === "openai" && (
          <div>
            <label className="text-xs text-zinc-400 uppercase tracking-wider">
              API Key
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full bg-zinc-900 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-200 mt-1 placeholder:text-zinc-500"
            />
          </div>
        )}
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col bg-zinc-900 rounded-lg border border-zinc-700 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-700">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-zinc-200">
              Chat
            </span>
            {currentProvider?.available ? (
              <span className="text-xs text-emerald-400">
                {selectedProvider} connected
              </span>
            ) : (
              <span className="text-xs text-zinc-400">
                no LLM detected
              </span>
            )}
          </div>
          <div className="flex gap-1">
            <button
              type="button"
              onClick={handleExport}
              disabled={messages.length === 0}
              className="p-1.5 rounded text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 disabled:opacity-30"
              title="Export chat"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={handleClear}
              disabled={messages.length === 0}
              className="p-1.5 rounded text-zinc-400 hover:text-red-400 hover:bg-zinc-800 disabled:opacity-30"
              title="Clear chat"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12 text-zinc-400">
              <Sparkles className="w-8 h-8 mx-auto mb-3 text-zinc-600" />
              <p className="text-sm">
                Ask about Glama scores, fleet health, or improvement plans.
              </p>
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {EXAMPLE_PROMPTS.slice(0, 4).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setInput(p)}
                    className="text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-full px-3 py-1.5 transition-colors"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex gap-3 ${
                m.role === "user" ? "justify-end" : ""
              }`}
            >
              {m.role === "assistant" && (
                <Bot className="w-5 h-5 text-blue-400 shrink-0 mt-1" />
              )}
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
                  m.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-zinc-800 text-zinc-200"
                }`}
              >
                <div className="whitespace-pre-wrap">{m.content}</div>
              </div>
              {m.role === "user" && (
                <User className="w-5 h-5 text-zinc-400 shrink-0 mt-1" />
              )}
            </div>
          ))}
          {sending && (
            <div className="flex gap-3">
              <Bot className="w-5 h-5 text-blue-400 shrink-0 mt-1" />
              <div className="bg-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-400">
                <span className="animate-pulse">Thinking...</span>
              </div>
            </div>
          )}
          {error && (
            <div className="text-center text-sm text-red-400">{error}</div>
          )}
          <div ref={endRef} />
        </div>

        {/* Input */}
        <div className="border-t border-zinc-700 p-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={
                currentProvider?.available
                  ? "Ask about Glama scores..."
                  : "No LLM detected. Start Ollama or LM Studio, or set OPENAI_API_KEY."
              }
              disabled={sending}
              className="flex-1 bg-zinc-950 border border-zinc-700 rounded-md px-3 py-2 text-sm text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={sending || !input.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white px-3 py-2 rounded-md transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
