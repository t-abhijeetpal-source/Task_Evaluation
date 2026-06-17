import Link from "next/link";
import { Card, Badge } from "@/components/ui/kit";
import { FileText, Download } from "lucide-react";
import { AGENTS } from "@/lib/data";

export const metadata = { title: "Reports — AgentOS" };

export default function ReportsPage() {
  const reports = AGENTS.filter((a) => a.evidence).map((a) => ({
    code: a.code, name: a.name, id: a.id, status: a.status,
    file: `${a.code}_record.md`, evidence: a.evidence!,
  }));
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Verification Reports</h1>
        <p className="text-sm text-[var(--muted)]">Evidence-backed records for every completed evaluation.</p>
      </div>
      <div className="card divide-y divide-[var(--border)] p-0">
        {reports.map((r) => (
          <div key={r.id} className="flex items-center gap-4 px-5 py-4">
            <FileText size={18} className="shrink-0 text-[var(--accent)]" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <Link href={`/agents/${r.id}`} className="text-sm font-medium hover:underline">{r.code} · {r.name}</Link>
                <Badge variant="status">{r.status}</Badge>
              </div>
              <p className="truncate text-xs text-[var(--muted)]">{r.evidence}</p>
            </div>
            <code className="hidden sm:block text-xs text-[var(--muted)]">{r.file}</code>
            <button className="glass grid h-9 w-9 place-items-center rounded-lg text-[var(--muted)] hover:text-[var(--fg)]"><Download size={15} /></button>
          </div>
        ))}
      </div>
    </div>
  );
}
