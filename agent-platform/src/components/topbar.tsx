"use client";
import { useTheme } from "next-themes";
import { Search, Moon, Sun, Bell, Command } from "lucide-react";
import { useUI } from "@/lib/store";
import { useEffect, useState } from "react";

export function Topbar() {
  const { setCmdk } = useUI();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <header className="sticky top-0 z-30 mb-6 flex items-center gap-3 px-1 pt-4">
      <button
        onClick={() => setCmdk(true)}
        className="glass group flex h-11 flex-1 items-center gap-3 rounded-xl px-3.5 text-sm text-[var(--muted)] transition hover:text-[var(--fg)]"
      >
        <Search size={16} />
        <span>Search agents, evaluations, docs…</span>
        <span className="ml-auto flex items-center gap-1 rounded-md border border-[var(--border)] px-1.5 py-0.5 text-[11px]">
          <Command size={11} /> K
        </span>
      </button>
      <button className="glass grid h-11 w-11 place-items-center rounded-xl text-[var(--muted)] transition hover:text-[var(--fg)]" aria-label="Notifications">
        <Bell size={17} />
      </button>
      <button
        onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        className="glass grid h-11 w-11 place-items-center rounded-xl text-[var(--muted)] transition hover:text-[var(--fg)]"
        aria-label="Toggle theme"
      >
        {mounted && theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
      </button>
      <div title="Abhijeet Pal" className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-[var(--accent-2)] to-[var(--accent)] text-sm font-semibold text-white">AP</div>
    </header>
  );
}
