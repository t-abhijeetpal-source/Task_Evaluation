import * as React from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("card p-5", className)} {...props} />;
}

const tierColor: Record<string, string> = {
  Basics: "text-emerald-400 bg-emerald-500/10 ring-emerald-500/20",
  Intermediate: "text-sky-400 bg-sky-500/10 ring-sky-500/20",
  Advanced: "text-violet-400 bg-violet-500/10 ring-violet-500/20",
  Infrastructure: "text-amber-400 bg-amber-500/10 ring-amber-500/20",
};
const statusColor: Record<string, string> = {
  Verified: "text-emerald-400 bg-emerald-500/10 ring-emerald-500/20",
  Passed: "text-emerald-400 bg-emerald-500/10 ring-emerald-500/20",
  "In Progress": "text-amber-400 bg-amber-500/10 ring-amber-500/20",
  Planned: "text-zinc-400 bg-zinc-500/10 ring-zinc-500/20",
};

export function Badge({
  children, variant = "default", className,
}: { children: React.ReactNode; variant?: "default" | "tier" | "status"; className?: string }) {
  const map = variant === "tier" ? tierColor : variant === "status" ? statusColor : {};
  const v = (map as Record<string, string>)[String(children)] ?? "text-[var(--muted)] bg-[var(--fg)]/5 ring-[var(--border)]";
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1", v, className)}>
      {children}
    </span>
  );
}

export function ScoreRing({ score, size = 44 }: { score: number; size?: number }) {
  const r = (size - 6) / 2;
  const c = 2 * Math.PI * r;
  const hue = score >= 90 ? "var(--accent-3)" : score >= 70 ? "var(--accent)" : "var(--accent-2)";
  return (
    <div className="relative shrink-0 grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth="4" />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={hue} strokeWidth="4"
          strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c - (score / 100) * c} />
      </svg>
      <span className="absolute inset-0 grid place-items-center text-[11px] font-semibold tabular-nums">{score}</span>
    </div>
  );
}
