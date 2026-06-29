import { create } from "zustand";
import type { Repo } from "./types";

type Page = "dashboard" | "report" | "tools" | "chat" | "help" | "settings";

interface AppState {
  repos: Repo[];
  loading: boolean;
  error: string | null;
  page: Page;
  selectedRepo: string | null;
  fetchRepos: () => Promise<void>;
  setPage: (p: Page) => void;
  setSelectedRepo: (name: string | null) => void;
}

export const useStore = create<AppState>((set) => ({
  repos: [],
  loading: true,
  error: null,
  page: "dashboard",
  selectedRepo: null,

  fetchRepos: async () => {
    set({ loading: true, error: null });
    try {
      const r = await fetch("/api/repos");
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      const repos = data.repos || data || [];
      set({ repos: Array.isArray(repos) ? repos : [], loading: false });
    } catch (e: unknown) {
      set({
        error: e instanceof Error ? e.message : "Failed to load repos",
        loading: false,
      });
    }
  },

  setPage: (page) => set({ page, selectedRepo: null }),

  setSelectedRepo: (name) => set({ selectedRepo: name }),
}));
