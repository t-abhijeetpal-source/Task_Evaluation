import Link from "next/link";
import { ArrowUpRight, Boxes, CheckCircle2, Gauge, Activity, FolderGit2, Star } from "lucide-react";
import { Counter } from "@/components/counter";
import { TrendChart, CategoryChart } from "@/components/charts";
import { AgentCard } from "@/components/agent-card";
import { Card } from "@/components/ui/kit";
import { AGENTS, METRICS, ACTIVITY } from "@/lib/data";

const stats = [
  { label: "Total Agents", value: METRICS.totalAgents, icon: Boxes, accent: "from-indigo-500/20 to-violet-500/10" },
  { label: "Completed", value: METRICS.completed, icon: CheckCircle2, accent: "from-emerald-500/20 to-teal-500/10" },
  { label: "Success Rate", value: METRICS.successRate, suffix: "%", icon: Gauge, accent: "from-cyan-500/20 to-sky-500/10" },
  { label: "Executions", value: METRICS.executions, icon: Activity, accent: "from-fuchsia-500/20 to-pink-500/10" },
  { label: "Projects", value: METRICS.projects, icon: FolderGit2, accent: "from-amber-500/20 to-orange-500/10" },
  { label: "Avg Score", value: METRICS.avgScore, icon: Star, accent: "from-violet-500/20 to-indigo-500/10" },
];

const kindColor: Record<string, string> = {
  perf: "bg-fuchsia-400", security: "bg-red-400", pass: "bg-emerald-400", verify: "bg-sky-400",
};

export default function Dashboard() {
  const top = [...AGENTS].sort((a, b) => b.score - a.score).slice(0, 3);
  return (
    <div className="space-y-8">
      <section className="card gradient-border relative overflow-hidden p-8">
        <div className="relative z-10 max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full glass px-3 py-1 text-xs text-[var(--muted)]">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" /> 24 agents · 85 tests passing
          </span>
          <h1 className="mt-4 text-3xl sm:text-4xl font-semibold tracking-tight">
            The <span className="gradient-text">AI Agent</span> Marketplace<br /> &amp; Evaluation Platform
          </h1>
          <p className="mt-3 text-[var(--muted)]">
            Browse, evaluate and ship production-grade coding agents — with prompts, execution flows,
            verification evidence and live metrics.
          </p>
          <div className="mt-6 flex gap-3">
            <Link href="/agents" className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-2)] px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-500/20 transition hover:brightness-110">
              Explore agents <ArrowUpRight size={16} />
            </Link>
            <Link href="/reports" className="glass inline-flex items-center rounded-xl px-4 py-2.5 text-sm font-medium transition hover:text-[var(--fg)]">
              View reports
            </Link>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.label} className="animate-in relative overflow-hidden">
              <div className={`absolute -right-6 -top-6 h-20 w-20 rounded-full bg-gradient-to-br ${s.accent} blur-2xl`} />
              <Icon size={18} className="text-[var(--accent)]" />
              <div className="mt-3 text-2xl font-semibold tabular-nums">
                <Counter value={s.value} suffix={s.suffix} />
              </div>
              <div className="text-xs text-[var(--muted)]">{s.label}</div>
            </Card>
          );
        })}
      </section>

      <section className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Evaluation Progress</h2>
            <span className="text-xs text-[var(--muted)]">last 6 months</span>
          </div>
          <TrendChart />
        </Card>
        <Card className="lg:col-span-2">
          <h2 className="mb-2 text-sm font-semibold">Performance by Category</h2>
          <CategoryChart />
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <h2 className="mb-4 text-sm font-semibold">Recent Activity</h2>
          <ul className="space-y-4">
            {ACTIVITY.map((a, i) => (
              <li key={i} className="flex gap-3">
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${kindColor[a.kind]}`} />
                <div className="min-w-0">
                  <p className="text-sm leading-snug"><span className="font-mono text-[var(--accent)]">{a.agent}</span> {a.text}</p>
                  <span className="text-[11px] text-[var(--muted)]">{a.time}</span>
                </div>
              </li>
            ))}
          </ul>
        </Card>
        <div className="lg:col-span-3">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Top-scoring agents</h2>
            <Link href="/agents" className="text-xs text-[var(--accent)] hover:underline">View all →</Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {top.map((a, i) => <AgentCard key={a.id} agent={a} index={i} />)}
          </div>
        </div>
      </section>
    </div>
  );
}
