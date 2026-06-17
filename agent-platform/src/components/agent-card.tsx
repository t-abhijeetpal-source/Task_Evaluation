"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { Star } from "lucide-react";
import type { Agent } from "@/lib/data";
import { Badge, ScoreRing } from "@/components/ui/kit";
import { useUI } from "@/lib/store";
import { cn } from "@/lib/utils";

export function AgentCard({ agent, index = 0 }: { agent: Agent; index?: number }) {
  const { favorites, toggleFavorite } = useUI();
  const fav = favorites.includes(agent.id);
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.03, 0.3), duration: 0.4 }}
      whileHover={{ y: -4 }}
    >
      <Link href={`/agents/${agent.id}`}
        className="card gradient-border group relative flex h-full flex-col gap-3 p-5 transition-shadow hover:shadow-xl hover:shadow-black/20">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-[var(--accent)]/20 to-[var(--accent-3)]/20 text-sm font-bold text-[var(--accent)] ring-1 ring-[var(--border)]">
              {agent.code}
            </span>
            <div>
              <h3 className="text-sm font-semibold leading-tight">{agent.name}</h3>
              <span className="text-[11px] text-[var(--muted)]">{agent.category}</span>
            </div>
          </div>
          <button
            onClick={(e) => { e.preventDefault(); toggleFavorite(agent.id); }}
            className={cn("rounded-lg p-1.5 transition", fav ? "text-amber-400" : "text-[var(--muted)] hover:text-[var(--fg)]")}
            aria-label="Favorite"
          >
            <Star size={16} fill={fav ? "currentColor" : "none"} />
          </button>
        </div>

        <p className="text-[13px] leading-relaxed text-[var(--muted)] line-clamp-2">{agent.summary}</p>

        <div className="mt-1 flex flex-wrap gap-1.5">
          {agent.tags.slice(0, 3).map((t) => (
            <span key={t} className="rounded-md bg-[var(--fg)]/5 px-2 py-0.5 text-[11px] text-[var(--muted)]">#{t}</span>
          ))}
        </div>

        <div className="mt-auto flex items-center justify-between pt-2">
          <div className="flex gap-1.5">
            <Badge variant="tier">{agent.tier}</Badge>
            <Badge variant="status">{agent.status}</Badge>
          </div>
          <ScoreRing score={agent.score} />
        </div>
      </Link>
    </motion.div>
  );
}
