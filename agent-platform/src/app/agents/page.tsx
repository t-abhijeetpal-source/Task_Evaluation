"use client";
import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Search, Download } from "lucide-react";
import { AGENTS, TIERS, agentSlug, agentDefinitionMd } from "@/lib/data";
import { Badge } from "@/components/ui/kit";
import { DocViewer } from "@/components/doc-viewer";
import { cn } from "@/lib/utils";

export default function AgentsPage() {
  const [tier, setTier] = useState<string>("All");
  const [q, setQ] = useState("");
  const [selectedId, setSelectedId] = useState(AGENTS[0].id);

  const list = useMemo(() => {
    const ql = q.toLowerCase();
    return AGENTS.filter(
      (a) =>
        (tier === "All" || a.tier === tier) &&
        (!ql || a.name.toLowerCase().includes(ql) || a.code.toLowerCase().includes(ql) || agentSlug(a).includes(ql))
    );
  }, [tier, q]);

  const currentId = list.some((a) => a.id === selectedId) ? selectedId : list[0]?.id;
  const current = AGENTS.find((a) => a.id === currentId) ?? AGENTS[0];

  const exportAll = () => {
    const md = AGENTS.map((a) => `# ${a.code} · ${a.name}\n\n${agentDefinitionMd(a)}\n\n---\n`).join("\n");
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const el = document.createElement("a");
    el.href = url; el.download = "agentos-all-agents.md"; el.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      {/* ---- Left: agent list pane ---- */}
      <aside className="lg:w-72 lg:shrink-0 space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold tracking-tight">Agent Library</h1>
          <button onClick={exportAll} title="Export all (.md)"
            className="glass grid h-8 w-8 place-items-center rounded-lg text-[var(--muted)] transition hover:text-[var(--fg)]">
            <Download size={15} />
          </button>
        </div>

        <div className="flex items-center gap-2 rounded-xl bg-[var(--fg)]/5 px-3">
          <Search size={15} className="text-[var(--muted)]" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search agents…"
            className="h-9 flex-1 bg-transparent text-sm outline-none placeholder:text-[var(--muted)]" />
        </div>

        <div>
          <div className="mb-2 px-1 text-[11px] font-medium uppercase tracking-wider text-[var(--muted)]">Filter</div>
          <div className="flex flex-wrap gap-1.5">
            {["All", ...TIERS].map((t) => (
              <button key={t} onClick={() => setTier(t)}
                className={cn("rounded-lg px-2.5 py-1 text-xs font-medium transition",
                  tier === t ? "bg-gradient-to-br from-[var(--accent)] to-[var(--accent-2)] text-white" : "bg-[var(--fg)]/5 text-[var(--muted)] hover:text-[var(--fg)]")}>
                {t}
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-2 px-1 text-[11px] font-medium uppercase tracking-wider text-[var(--muted)]">Select agent ({list.length})</div>
          <div className="space-y-1.5 lg:max-h-[calc(100vh-20rem)] lg:overflow-y-auto scrollbar-thin pr-1">
            {list.map((a) => {
              const active = a.id === currentId;
              return (
                <button key={a.id} onClick={() => setSelectedId(a.id)}
                  className={cn("relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition",
                    active ? "glass ring-1 ring-[var(--accent)]/40" : "hover:bg-[var(--fg)]/5")}>
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-[var(--accent)]/20 to-[var(--accent-3)]/20 text-[11px] font-bold text-[var(--accent)] ring-1 ring-[var(--border)]">{a.code}</span>
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium leading-tight">{a.name}</div>
                    <div className="truncate font-mono text-[11px] text-[var(--muted)]">{agentSlug(a)}</div>
                  </div>
                </button>
              );
            })}
            {list.length === 0 && <div className="px-3 py-6 text-center text-sm text-[var(--muted)]">No agents match.</div>}
          </div>
        </div>
      </aside>

      {/* ---- Right: detail panel ---- */}
      <motion.section key={current.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}
        className="min-w-0 flex-1 space-y-5">
        <div className="card gradient-border p-6">
          <div className="flex flex-wrap items-center gap-2">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-[var(--accent)]/25 to-[var(--accent-3)]/20 text-sm font-bold text-[var(--accent)] ring-1 ring-[var(--border)]">{current.code}</span>
            <Badge variant="tier">{current.tier}</Badge>
            <Badge variant="status">{current.status}</Badge>
            <Badge>{current.difficulty}</Badge>
            <span className="ml-auto text-xs text-[var(--muted)]">{current.category}</span>
          </div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight">{current.name}</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">Browse the agent definition, or preview a sample report produced when it runs on a repository.</p>
          <div className="mt-1 font-mono text-[11px] text-[var(--muted)]">repo-{agentSlug(current)}</div>
        </div>

        <DocViewer agent={current} />
      </motion.section>
    </div>
  );
}
