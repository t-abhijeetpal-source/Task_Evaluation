"use client";
import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Download, Check, FileText, MonitorPlay } from "lucide-react";
import type { Agent } from "@/lib/data";
import { agentDefinitionMd, agentDemoOutputMd, agentMetadata, agentSlug } from "@/lib/data";
import { cn } from "@/lib/utils";

type DocMode = "Agent Definition" | "Demo Output";
type View = "Preview" | "Raw";

export function DocViewer({ agent }: { agent: Agent }) {
  const [docMode, setDocMode] = useState<DocMode>("Agent Definition");
  const [view, setView] = useState<View>("Preview");
  const [copied, setCopied] = useState(false);

  const { md, file } = useMemo(() => {
    const slug = agentSlug(agent);
    return docMode === "Agent Definition"
      ? { md: agentDefinitionMd(agent), file: `${agent.code}-${slug}.agent.md` }
      : { md: agentDemoOutputMd(agent), file: `${agent.code}-${slug}.demo.md` };
  }, [agent, docMode]);

  const copy = async () => { await navigator.clipboard.writeText(md); setCopied(true); setTimeout(() => setCopied(false), 1800); };
  const download = () => {
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = file; a.click();
    URL.revokeObjectURL(url);
  };

  const lines = md.split("\n");

  return (
    <div className="card overflow-hidden">
      {/* toolbar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[var(--border)] p-3">
        <Segmented<DocMode> value={docMode} onChange={setDocMode} options={[
          { v: "Agent Definition", icon: <FileText size={14} /> },
          { v: "Demo Output", icon: <MonitorPlay size={14} /> },
        ]} />
        <div className="ml-auto flex items-center gap-2">
          <Segmented<View> value={view} onChange={setView} options={[{ v: "Preview" }, { v: "Raw" }]} small />
          <button onClick={copy}
            className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-br from-[var(--accent)] to-[var(--accent-2)] px-3 py-1.5 text-xs font-medium text-white transition hover:brightness-110">
            {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? "Copied" : "Copy .md"}
          </button>
          <button onClick={download}
            className="glass inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition hover:text-[var(--fg)]">
            <Download size={14} /> Download
          </button>
        </div>
      </div>

      <div className="font-mono text-[11px] text-[var(--muted)] px-4 pt-2">{file}</div>

      {/* body */}
      {view === "Preview" ? (
        <div className="md-prose max-h-[58vh] overflow-auto scrollbar-thin px-5 py-3 text-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
        </div>
      ) : (
        <div className="max-h-[58vh] overflow-auto scrollbar-thin font-mono text-[12.5px] leading-relaxed">
          <table className="w-full border-collapse">
            <tbody>
              {lines.map((ln, i) => (
                <tr key={i} className="hover:bg-[var(--fg)]/[0.03]">
                  <td className="select-none border-r border-[var(--border)] px-3 text-right align-top text-[var(--muted)] tabular-nums w-12">{i + 1}</td>
                  <td className="whitespace-pre-wrap break-words px-4 py-px align-top">{ln || " "}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* metadata (demo output) */}
      {docMode === "Demo Output" && (
        <div className="border-t border-[var(--border)] p-5">
          <h3 className="mb-3 text-sm font-semibold">Metadata</h3>
          <div className="overflow-hidden rounded-xl border border-[var(--border)]">
            <table className="w-full text-sm">
              <tbody className="divide-y divide-[var(--border)]">
                {agentMetadata(agent).map(([k, v]) => (
                  <tr key={k}>
                    <td className="w-40 bg-[var(--fg)]/[0.03] px-4 py-2.5 font-medium text-[var(--muted)]">{k}</td>
                    <td className="px-4 py-2.5 font-mono text-[12.5px]">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function Segmented<T extends string>({
  value, onChange, options, small,
}: { value: T; onChange: (v: T) => void; options: { v: T; icon?: React.ReactNode }[]; small?: boolean }) {
  return (
    <div className="inline-flex rounded-lg bg-[var(--fg)]/5 p-0.5">
      {options.map((o) => (
        <button key={o.v} onClick={() => onChange(o.v)}
          className={cn("inline-flex items-center gap-1.5 rounded-md font-medium transition",
            small ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-xs",
            value === o.v ? "bg-[var(--bg-elev)] text-[var(--fg)] shadow-sm ring-1 ring-[var(--border)]" : "text-[var(--muted)] hover:text-[var(--fg)]")}>
          {o.icon} {o.v}
        </button>
      ))}
    </div>
  );
}
