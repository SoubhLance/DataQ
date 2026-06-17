import { Link, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard, Upload, Table2, Copy, AlertTriangle, ScatterChart,
  Tags, Sliders, GitBranch, BarChart3, Sparkles, Workflow, FileText, Settings, Database,
} from "lucide-react";

type Item = {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  exact?: boolean;
  glow?: boolean;
};

const items: Item[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { to: "/dashboard/upload", label: "Upload Dataset", icon: Upload },
  { to: "/dashboard/inspector", label: "Dataset Inspector", icon: Table2 },
  { to: "/dashboard/duplicates", label: "Duplicates", icon: Copy },
  { to: "/dashboard/missing", label: "Missing Values", icon: AlertTriangle },
  { to: "/dashboard/outliers", label: "Outliers", icon: ScatterChart },
  { to: "/dashboard/encoding", label: "Encoding", icon: Tags },
  { to: "/dashboard/scaling", label: "Scaling", icon: Sliders },
  { to: "/dashboard/correlation", label: "Correlation", icon: GitBranch },
  { to: "/dashboard/visualizations", label: "Visualizations", icon: BarChart3 },
  { to: "/dashboard/agent", label: "AI Agent", icon: Sparkles, glow: true },
  { to: "/dashboard/pipeline", label: "Pipeline", icon: Workflow },
  { to: "/dashboard/reports", label: "Reports", icon: FileText },
  { to: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function DashboardSidebar() {
  const { pathname } = useLocation();

  return (
    <aside className="hidden lg:flex fixed left-0 top-0 z-40 h-screen w-64 flex-col border-r border-border/60 bg-card/40 backdrop-blur-xl">
      <div className="px-5 pt-6 pb-4 flex items-center gap-2">
        <div className="grid place-items-center w-9 h-9 rounded-lg bg-gradient-brand text-white shadow-[var(--glow-orange)]">
          <Database className="w-4 h-4" />
        </div>
        <div className="leading-tight">
          <div className="font-bold tracking-wide">DataQ</div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Workspace</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
        {items.map((item, i) => {
          const active = item.exact ? pathname === item.to : pathname.startsWith(item.to);
          const Icon = item.icon;
          return (
            <motion.div
              key={item.to}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.025, duration: 0.3 }}
            >
              <Link
                to={item.to as string}
                className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                  active
                    ? "bg-gradient-to-r from-primary/20 to-destructive/10 text-foreground border border-primary/30 shadow-[0_0_20px_rgba(255,122,0,0.15)]"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                }`}
              >
                {active && (
                  <motion.span
                    layoutId="sidebar-active-bar"
                    className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-0.5 rounded-r bg-gradient-brand shadow-[0_0_10px_var(--brand-orange)]"
                  />
                )}
                <Icon className={`w-4 h-4 ${item.glow ? "text-[var(--brand-amber)]" : ""}`} />
                <span>{item.label}</span>
                {item.glow && (
                  <span className="ml-auto text-[9px] uppercase tracking-widest text-primary">AI</span>
                )}
              </Link>
            </motion.div>
          );
        })}
      </nav>

      <div className="m-3 rounded-xl border border-primary/30 bg-gradient-to-br from-primary/10 to-destructive/10 p-4">
        <div className="text-xs uppercase tracking-widest text-primary mb-1">Pro Tip</div>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Use the AI Agent to auto-generate cleaning pipelines for any dataset.
        </p>
      </div>
    </aside>
  );
}