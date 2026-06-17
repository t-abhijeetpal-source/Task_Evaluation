"use client";
import { useState } from "react";
import { Copy, Download, Check, Maximize2, Minimize2, WrapText } from "lucide-react";
import { cn } from "@/lib/utils";

export function PromptViewer({ prompt, title }: { prompt: string; title: string }) {
  const [copied, setCopied] = useState(false);
  const [full, setFull] = useState(false);
  const [wrap, setWrap] = useState(true);
  const lines = prompt.split("\n");

  const copy = async () => {
    await navigator.clipboard.writeText(prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };
  const download = () => {
    const blob = new Blob([prompt], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `${title}.md`; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={cn("card overflow-hidden", full && "fixed inset-4 z-50 m-0 shadow-2xl")}>
      <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-2.5">
        <div className="flex items-center gap-2 text-xs text-[var(--muted)]">
          <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-amber-400/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/70" />
          <span className="ml-2 font-mono">{title}.md</span>
        </div>
        <div className="flex items-center gap-1">
          <IconBtn onClick={() => setWrap(!wrap)} label="Wrap"><WrapText size={15} /></IconBtn>
          <IconBtn onClick={download} label="Download"><Download size={15} /></IconBtn>
          <IconBtn onClick={copy} label="Copy">{copied ? <Check size={15} className="text-emerald-400" /> : <Copy size={15} />}</IconBtn>
          <IconBtn onClick={() => setFull(!full)} label="Fullscreen">{full ? <Minimize2 size={15} /> : <Maximize2 size={15} />}</IconBtn>
        </div>
      </div>
      <div className={cn("overflow-auto scrollbar-thin font-mono text-[12.5px] leading-relaxed", full ? "h-[calc(100%-44px)]" : "max-h-[60vh]")}>
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((ln, i) => (
              <tr key={i} className="hover:bg-[var(--fg)]/[0.03]">
                <td className="select-none border-r border-[var(--border)] px-3 text-right align-top text-[var(--muted)] tabular-nums w-12">{i + 1}</td>
                <td className={cn("px-4 py-px align-top", wrap ? "whitespace-pre-wrap break-words" : "whitespace-pre")}>{ln || " "}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function IconBtn({ children, onClick, label }: { children: React.ReactNode; onClick: () => void; label: string }) {
  return (
    <button onClick={onClick} aria-label={label}
      className="grid h-8 w-8 place-items-center rounded-lg text-[var(--muted)] transition hover:bg-[var(--fg)]/5 hover:text-[var(--fg)]">
      {children}
    </button>
  );
}
