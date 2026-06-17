"use client";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import { CommandPalette } from "./command-palette";

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="aurora flex min-h-screen">
      <Sidebar />
      <div className="flex-1 min-w-0 px-4 sm:px-6 lg:px-8 pb-16">
        <Topbar />
        <AnimatePresence mode="wait">
          <motion.main
            key={path}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="mx-auto max-w-7xl"
          >
            {children}
          </motion.main>
        </AnimatePresence>
      </div>
      <CommandPalette />
    </div>
  );
}
