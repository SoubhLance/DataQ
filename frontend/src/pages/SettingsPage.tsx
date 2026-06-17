import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useState } from "react";
import { Moon, Sun, Clock, Bell, Info, Database } from "lucide-react";
import { useTheme } from "@/components/theme-provider";
import { PageHeader } from "@/components/dashboard/page-header";



export default function SettingsPage() {
  useEffect(() => {
    document.title = "Settings — DataQ";
  }, []);
  const { theme, toggle } = useTheme();
  const [timeout_, setTimeout_] = useState(30);
  const [notif, setNotif] = useState({ email: true, push: false, weekly: true });

  return (
    <div>
      <PageHeader eyebrow="Account" title="Settings" description="Manage your DataQ workspace preferences and session behavior." />

      <div className="grid lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card rounded-2xl p-6">
          <div className="text-[10px] uppercase tracking-widest text-primary mb-3 flex items-center gap-1.5">{theme === "dark" ? <Moon className="w-3 h-3" /> : <Sun className="w-3 h-3" />}Theme</div>
          <h3 className="font-semibold">Appearance</h3>
          <p className="text-xs text-muted-foreground mt-1 mb-4">Switch between cinematic dark and clean light mode.</p>
          <div className="flex gap-2">
            {(["dark", "light"] as const).map((t) => (
              <button key={t} onClick={() => { if (theme !== t) toggle(); }} className={`px-4 py-2 rounded-lg text-xs capitalize transition ${theme === t ? "bg-gradient-brand text-white shadow-[var(--glow-orange)]" : "border border-border hover:border-primary"}`}>{t}</button>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }} className="glass-card rounded-2xl p-6">
          <div className="text-[10px] uppercase tracking-widest text-primary mb-3 flex items-center gap-1.5"><Clock className="w-3 h-3" />Session</div>
          <h3 className="font-semibold">Session Timeout</h3>
          <p className="text-xs text-muted-foreground mt-1 mb-4">Sign out automatically after {timeout_} minutes of inactivity.</p>
          <input type="range" min={5} max={120} step={5} value={timeout_} onChange={(e) => setTimeout_(Number(e.target.value))} className="w-full accent-[var(--brand-orange)]" />
          <div className="flex justify-between text-[10px] text-muted-foreground mt-1"><span>5m</span><span className="text-primary font-mono">{timeout_} min</span><span>120m</span></div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card rounded-2xl p-6">
          <div className="text-[10px] uppercase tracking-widest text-primary mb-3 flex items-center gap-1.5"><Bell className="w-3 h-3" />Notifications</div>
          <h3 className="font-semibold">Channels</h3>
          <div className="mt-4 space-y-3">
            {(["email", "push", "weekly"] as const).map((k) => (
              <label key={k} className="flex items-center justify-between rounded-xl border border-border/60 px-4 py-3 cursor-pointer hover:border-primary/40">
                <span className="text-sm capitalize">{k} {k === "weekly" && "digest"}</span>
                <button onClick={() => setNotif({ ...notif, [k]: !notif[k] })} className={`relative w-10 h-5 rounded-full transition ${notif[k] ? "bg-gradient-brand" : "bg-secondary"}`}>
                  <span className={`absolute top-0.5 ${notif[k] ? "left-5" : "left-0.5"} w-4 h-4 rounded-full bg-white transition-all`} />
                </button>
              </label>
            ))}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="glass-card rounded-2xl p-6 border-primary/30">
          <div className="text-[10px] uppercase tracking-widest text-primary mb-3 flex items-center gap-1.5"><Info className="w-3 h-3" />About</div>
          <div className="flex items-center gap-3">
            <div className="grid place-items-center w-12 h-12 rounded-xl bg-gradient-brand text-white shadow-[var(--glow-orange)]"><Database className="w-5 h-5" /></div>
            <div>
              <h3 className="font-bold">DataQ</h3>
              <p className="text-xs text-muted-foreground">v1.0.0 · Built by Team Curious Minds</p>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-4 leading-relaxed">
            AI-powered dataset quality checker and preprocessing platform. Transform raw data into ML-ready intelligence.
          </p>
        </motion.div>
      </div>
    </div>
  );
}