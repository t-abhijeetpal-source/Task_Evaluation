import { Card } from "@/components/ui/kit";
import { BookOpen, Search, Hash } from "lucide-react";

export const metadata = { title: "Documentation — AgentOS" };

const sections = [
  { title: "Getting Started", items: ["Platform overview", "Quickstart", "Running an agent", "Reading evaluation reports"] },
  { title: "Agent Authoring", items: ["Prompt structure", "Inputs & outputs contract", "Evidence rules (VERIFIED/INFERRED)", "Verification checklist"] },
  { title: "Evaluation", items: ["Scoring matrix", "Risk levels", "Verification logs", "Agent vs Verified split"] },
  { title: "Infrastructure", items: ["Reproducible env (mise)", "CI pipeline", "Docker Compose", "Terraform"] },
];

export default function DocumentationPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Documentation Center</h1>
        <p className="text-sm text-[var(--muted)]">Searchable, versioned docs with table of contents and code highlighting.</p>
      </div>
      <div className="card flex items-center gap-2 rounded-xl px-4">
        <Search size={16} className="text-[var(--muted)]" />
        <input placeholder="Search documentation…" className="h-11 flex-1 bg-transparent text-sm outline-none placeholder:text-[var(--muted)]" />
        <span className="text-xs text-[var(--muted)]">v2.0</span>
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        {sections.map((s) => (
          <Card key={s.title}>
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold"><BookOpen size={15} className="text-[var(--accent)]" /> {s.title}</div>
            <ul className="space-y-2">
              {s.items.map((it) => (
                <li key={it} className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-[var(--muted)] transition hover:bg-[var(--fg)]/5 hover:text-[var(--fg)]">
                  <Hash size={13} /> {it}
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
      <Card>
        <pre className="overflow-auto scrollbar-thin rounded-xl bg-[var(--fg)]/5 p-4 font-mono text-xs leading-relaxed">
{`# Quickstart — run any agent locally
make bootstrap          # pin runtimes, install deps, generate .env, test
make test               # full suite (85 tests across Python/Node/Rust)

# Copy a prompt and run it in your coding agent
#   Agents → pick an agent → Copy Prompt → paste into Claude Code / Cursor`}
        </pre>
      </Card>
    </div>
  );
}
