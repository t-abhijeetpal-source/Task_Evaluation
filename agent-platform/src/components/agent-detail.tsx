"use client";
import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Share2, Star, GitBranch } from "lucide-react";
import type { Agent } from "@/lib/data";
import { Badge, ScoreRing } from "@/components/ui/kit";
import { DocViewer } from "@/components/doc-viewer";
import { AgentCard } from "@/components/agent-card";
import { useUI } from "@/lib/store";
import { cn } from "@/lib/utils";

const TABS = ["Overview", "Execution Flow", "Inputs", "Outputs", "Verification", "Related", "Versions"] as const;
type Tab = (typeof TABS)[number];

export function AgentDetail({ agent, related }: { agent: Agent; related: Agent[] }) {
  const [tab, setTab] = useState<Tab>("Overview");
  const { favorites, toggleFavorite } = useUI();
  const fav = favorites.includes(agent.id);

  return (
    <div className="space-y-6">
      <Link href="/agents" className="inline-flex items-center gap-1.5 text-sm text-[var(--muted)] hover:text-[var(--fg)]">
        <ArrowLeft size={15} /> Back to library
      </Link>

      {/* Header */}
      <div className="card gradient-border flex flex-wrap items-center justify-between gap-4 p-6">
        <div className="flex items-center gap-4">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-[var(--accent)]/25 to-[var(--accent-3)]/20 text-lg font-bold text-[var(--accent)] ring-1 ring-[var(--border)]">{agent.code}</span>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{agent.name}</h1>
            <div className="mt-1.5 flex flex-wrap items-center gap-2">
              <Badge variant="tier">{agent.tier}</Badge>
              <Badge variant="status">{agent.status}</Badge>
              <Badge>{agent.difficulty}</Badge>
              <span className="text-xs text-[var(--muted)]">{agent.category}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          <ScoreRing score={agent.score} size={52} />
          <button onClick={() => toggleFavorite(agent.id)} className={cn("glass grid h-10 w-10 place-items-center rounded-xl", fav ? "text-amber-400" : "text-[var(--muted)] hover:text-[var(--fg)]")}>
            <Star size={17} fill={fav ? "currentColor" : "none"} />
          </button>
          <button onClick={() => navigator.share?.({ title: agent.name, text: agent.summary }).catch(() => {})}
            className="glass grid h-10 w-10 place-items-center rounded-xl text-[var(--muted)] hover:text-[var(--fg)]">
            <Share2 size={16} />
          </button>
        </div>
      </div>

      {/* Split screen */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left: tabbed info */}
        <div className="card p-0 overflow-hidden">
          <div className="flex flex-wrap gap-1 border-b border-[var(--border)] p-2">
            {TABS.map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={cn("relative rounded-lg px-3 py-1.5 text-xs font-medium transition",
                  tab === t ? "text-[var(--fg)]" : "text-[var(--muted)] hover:text-[var(--fg)]")}>
                {tab === t && <motion.span layoutId="tab-pill" className="absolute inset-0 -z-10 rounded-lg bg-[var(--fg)]/8" />}
                {t}
              </button>
            ))}
          </div>
          <div className="p-5 text-sm leading-relaxed min-h-[20rem]">
            {tab === "Overview" && <p className="text-[var(--muted)]">{agent.description}</p>}

            {tab === "Execution Flow" && (
              <ol className="space-y-3">
                {agent.flow.map((s, i) => (
                  <li key={i} className="flex gap-3">
                    <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-[var(--accent)]/15 text-[11px] font-semibold text-[var(--accent)]">{i + 1}</span>
                    <span className="pt-0.5">{s}</span>
                  </li>
                ))}
              </ol>
            )}

            {tab === "Inputs" && (
              <div className="space-y-3">
                {agent.inputs.map((inp) => (
                  <div key={inp.name} className="rounded-xl bg-[var(--fg)]/5 p-3">
                    <div className="flex items-center gap-2">
                      <code className="text-[var(--accent)]">{inp.name}</code>
                      <span className="text-[11px] text-[var(--muted)]">{inp.type}</span>
                      {inp.required && <Badge className="!text-rose-400 !bg-rose-500/10">required</Badge>}
                    </div>
                    <p className="mt-1 text-[var(--muted)]">{inp.note}</p>
                  </div>
                ))}
              </div>
            )}

            {tab === "Outputs" && (
              <ul className="space-y-2">
                {agent.outputs.map((o) => (
                  <li key={o} className="flex items-center gap-2 rounded-lg bg-[var(--fg)]/5 px-3 py-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-[var(--accent-3)]" /> <code className="text-xs">{o}</code>
                  </li>
                ))}
              </ul>
            )}

            {tab === "Verification" && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  {agent.metrics.map((m) => (
                    <div key={m.label} className="rounded-xl bg-[var(--fg)]/5 p-3">
                      <div className="text-xs text-[var(--muted)]">{m.label}</div>
                      <div className="mt-0.5 text-sm font-semibold">{m.value}</div>
                    </div>
                  ))}
                </div>
                {agent.evidence && (
                  <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-3 text-emerald-300/90">
                    <div className="mb-1 text-xs font-semibold uppercase tracking-wide">Verified evidence</div>
                    {agent.evidence}
                  </div>
                )}
              </div>
            )}

            {tab === "Related" && (
              <div className="grid gap-3 sm:grid-cols-2">
                {related.map((r, i) => <AgentCard key={r.id} agent={r} index={i} />)}
              </div>
            )}

            {tab === "Versions" && (
              <ul className="space-y-3">
                {[{ v: "v2.0", note: "Hardened + verified", cur: true }, { v: "v1.1", note: "Added evidence + metrics" }, { v: "v1.0", note: "Initial release" }].map((h) => (
                  <li key={h.v} className="flex items-center gap-3">
                    <GitBranch size={14} className="text-[var(--muted)]" />
                    <code className={cn("text-xs", h.cur && "text-[var(--accent)]")}>{h.v}</code>
                    <span className="text-[var(--muted)]">{h.note}</span>
                    {h.cur && <Badge variant="status">Verified</Badge>}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Right: document viewer (definition / demo output, preview / raw) */}
        <div>
          <DocViewer agent={agent} />
        </div>
      </div>
    </div>
  );
}
