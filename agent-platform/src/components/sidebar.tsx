"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Boxes, FolderGit2, BookOpen, FileText, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "Agents", icon: Boxes },
  { href: "/projects", label: "Projects", icon: FolderGit2 },
  { href: "/documentation", label: "Documentation", icon: BookOpen },
  { href: "/reports", label: "Reports", icon: FileText },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col gap-2 p-4 sticky top-0 h-screen">
      <Link href="/" className="flex items-center gap-2.5 px-2 py-3">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-[var(--accent)] to-[var(--accent-3)] text-white shadow-lg shadow-indigo-500/20">
          <Sparkles size={18} />
        </span>
        <div className="leading-tight">
          <div className="text-sm font-semibold">AgentOS</div>
          <div className="text-[11px] text-[var(--muted)]">Evaluation Platform</div>
        </div>
      </Link>

      <nav className="mt-2 flex flex-col gap-1">
        {nav.map((n) => {
          const active = n.href === "/" ? path === "/" : path.startsWith(n.href);
          const Icon = n.icon;
          return (
            <Link key={n.href} href={n.href}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors",
                active ? "text-[var(--fg)]" : "text-[var(--muted)] hover:text-[var(--fg)]"
              )}>
              {active && (
                <motion.span layoutId="nav-active" className="absolute inset-0 -z-10 rounded-xl glass" transition={{ type: "spring", stiffness: 400, damping: 32 }} />
              )}
              <Icon size={17} className={cn("transition-colors", active && "text-[var(--accent)]")} />
              {n.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto card p-3 text-xs text-[var(--muted)]">
        <div className="flex items-center gap-2 font-medium text-[var(--fg)]"><span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" /> All systems green</div>
        <p className="mt-1">24 agents · 85 tests passing</p>
      </div>
    </aside>
  );
}
