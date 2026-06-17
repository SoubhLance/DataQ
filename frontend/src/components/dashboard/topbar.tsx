import { motion } from "framer-motion";
import { Search, Bell, Moon, Sun, ChevronDown, Database } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useTheme } from "@/components/theme-provider";
import { useSession } from "@/context/SessionContext";

export function DashboardTopbar() {
  const { theme, toggle } = useTheme();
  const { filename } = useSession();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 h-16 border-b border-border/60 bg-background/70 backdrop-blur-xl">
      <div className="h-full px-6 flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-primary/30 bg-primary/5 text-xs">
          <Database className="w-3.5 h-3.5 text-primary" />
          <span className="text-muted-foreground">Current dataset</span>
          <span className="font-semibold truncate max-w-[150px]">
            {filename || "No active session"}
          </span>
        </div>


        <div className="flex-1 max-w-xl">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              placeholder="Search columns, operations, datasets…"
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-secondary/60 border border-border focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none text-sm transition"
            />
            <kbd className="hidden md:inline absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground border border-border rounded px-1.5 py-0.5">⌘K</kbd>
          </div>
        </div>

        <button
          onClick={toggle}
          aria-label="Toggle theme"
          className="grid place-items-center w-9 h-9 rounded-lg border border-border hover:border-primary transition"
        >
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        <button className="relative grid place-items-center w-9 h-9 rounded-lg border border-border hover:border-primary transition">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-destructive shadow-[0_0_8px_var(--brand-red)]" />
        </button>

        <div className="relative">
          <button
            onClick={() => setOpen((o) => !o)}
            className="flex items-center gap-2 pl-1 pr-3 py-1 rounded-xl border border-border hover:border-primary transition"
          >
            <div className="grid place-items-center w-7 h-7 rounded-lg bg-gradient-brand text-white text-xs font-bold">D</div>
            <span className="hidden md:inline text-sm">demo@dataq.ai</span>
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
          </button>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="absolute right-0 mt-2 w-56 rounded-xl border border-border bg-popover/95 backdrop-blur-xl shadow-xl p-2 text-sm"
            >
              <div className="px-3 py-2 text-xs text-muted-foreground">Signed in as</div>
              <div className="px-3 pb-2 font-medium">demo@dataq.ai</div>
              <hr className="border-border my-1" />
              <Link to="/dashboard/settings" className="block px-3 py-2 rounded hover:bg-secondary/60">Settings</Link>
              <Link to="/" className="block px-3 py-2 rounded hover:bg-secondary/60 text-destructive">Sign out</Link>
            </motion.div>
          )}
        </div>
      </div>
    </header>
  );
}