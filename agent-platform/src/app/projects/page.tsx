import { Card } from "@/components/ui/kit";
import { PROJECTS } from "@/lib/data";

export const metadata = { title: "Projects — AgentOS" };

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Project Showcase</h1>
        <p className="text-sm text-[var(--muted)]">Real systems built and verified by the agents — stack, metrics and links.</p>
      </div>
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {PROJECTS.map((p) => (
          <Card key={p.name} className="gradient-border flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{p.name}</h3>
              <span className="rounded-md bg-[var(--accent)]/15 px-2 py-0.5 text-xs font-mono text-[var(--accent)]">{p.tier}</span>
            </div>
            <p className="text-sm text-[var(--muted)]">{p.desc}</p>
            <div className="flex flex-wrap gap-1.5">
              {p.stack.map((s) => <span key={s} className="rounded-md bg-[var(--fg)]/5 px-2 py-0.5 text-[11px]">{s}</span>)}
            </div>
            <div className="mt-auto border-t border-[var(--border)] pt-3">
              <span className="text-xs font-medium text-emerald-400">{p.metric}</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
