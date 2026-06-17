"use client";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Search, CornerDownLeft } from "lucide-react";
import { useUI } from "@/lib/store";
import { AGENTS } from "@/lib/data";

const navItems = [
  { label: "Dashboard", href: "/" },
  { label: "Agents", href: "/agents" },
  { label: "Projects", href: "/projects" },
  { label: "Documentation", href: "/documentation" },
  { label: "Reports", href: "/reports" },
];

export function CommandPalette() {
  const { cmdkOpen, setCmdk } = useUI();
  const [q, setQ] = useState("");
  const router = useRouter();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCmdk(!cmdkOpen);
      }
      if (e.key === "Escape") setCmdk(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [cmdkOpen, setCmdk]);

  const results = useMemo(() => {
    const ql = q.toLowerCase();
    const nav = navItems.filter((n) => n.label.toLowerCase().includes(ql)).map((n) => ({ ...n, group: "Navigate" }));
    const agents = AGENTS.filter(
      (a) => a.name.toLowerCase().includes(ql) || a.code.toLowerCase().includes(ql) || a.tags.some((t) => t.includes(ql))
    ).slice(0, 6).map((a) => ({ label: `${a.code} · ${a.name}`, href: `/agents/${a.id}`, group: "Agents" }));
    return [...nav, ...agents];
  }, [q]);

  const go = (href: string) => { setCmdk(false); setQ(""); router.push(href); };

  return (
    <AnimatePresence>
      {cmdkOpen && (
        <motion.div className="fixed inset-0 z-[60] flex items-start justify-center p-4 pt-[12vh]"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setCmdk(false)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -8 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.97 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
            className="glass relative w-full max-w-xl overflow-hidden rounded-2xl shadow-2xl">
            <div className="flex items-center gap-3 border-b border-[var(--border)] px-4">
              <Search size={18} className="text-[var(--muted)]" />
              <input autoFocus value={q} onChange={(e) => setQ(e.target.value)}
                placeholder="Type a command or search…"
                className="h-14 flex-1 bg-transparent text-sm outline-none placeholder:text-[var(--muted)]" />
              <kbd className="rounded border border-[var(--border)] px-1.5 py-0.5 text-[11px] text-[var(--muted)]">ESC</kbd>
            </div>
            <div className="max-h-80 overflow-y-auto scrollbar-thin p-2">
              {results.length === 0 && <div className="px-3 py-8 text-center text-sm text-[var(--muted)]">No results</div>}
              {results.map((r, i) => (
                <button key={i} onClick={() => go(r.href)}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-left hover:bg-[var(--fg)]/5">
                  <span className="text-[10px] uppercase tracking-wide text-[var(--muted)] w-16">{r.group}</span>
                  <span className="flex-1">{r.label}</span>
                  <CornerDownLeft size={13} className="text-[var(--muted)] opacity-0 group-hover:opacity-100" />
                </button>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
