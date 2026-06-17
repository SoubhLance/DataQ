import { motion } from "framer-motion";
import { Moon, Sun, Database } from "lucide-react";
import { useTheme } from "@/components/theme-provider";

export function Navbar() {
  const { theme, toggle } = useTheme();
  return (
    <motion.header
      initial={{ y: -30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.7, ease: "easeOut" }}
      className="fixed top-4 left-1/2 z-50 -translate-x-1/2 w-[min(1100px,92%)]"
    >
      <div className="glass-card flex items-center justify-between rounded-2xl px-5 py-3">
        <div className="flex items-center gap-2">
          <div className="grid place-items-center w-8 h-8 rounded-lg bg-gradient-brand text-white shadow-[var(--glow-orange)]">
            <Database className="w-4 h-4" />
          </div>
          <span className="font-bold tracking-wide">DataQ</span>
        </div>
        <nav className="hidden md:flex items-center gap-7 text-sm text-muted-foreground">
          <a href="#features" className="hover:text-foreground transition">Features</a>
          <a href="#how" className="hover:text-foreground transition">How it works</a>
          <a href="#agent" className="hover:text-foreground transition">AI Agent</a>
          <a href="#grid" className="hover:text-foreground transition">Capabilities</a>
        </nav>
        <button
          onClick={toggle}
          aria-label="Toggle theme"
          className="grid place-items-center w-9 h-9 rounded-lg border border-border hover:border-primary transition"
        >
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </motion.header>
  );
}