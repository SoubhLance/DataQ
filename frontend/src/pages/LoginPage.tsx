import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Database, Loader2, ArrowRight } from "lucide-react";
import { FloatingParticles } from "@/components/floating-particles";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("demo@dataq.ai");
  const [password, setPassword] = useState("demo1234");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "Sign in — DataQ";
  }, []);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => navigate("/dashboard"), 700);
  };

  return (
    <main className="relative min-h-screen w-full overflow-hidden bg-background text-foreground grid place-items-center px-6">
      <div className="absolute inset-0 grid-bg opacity-50" />
      <div className="pointer-events-none absolute -top-32 left-1/2 -translate-x-1/2 h-[500px] w-[700px] rounded-full bg-[var(--brand-orange)] opacity-20 blur-[120px]" />
      <FloatingParticles count={18} accent />

      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.2, 0.8, 0.2, 1] }}
        className="relative z-10 w-full max-w-md glass-card rounded-3xl p-8 shadow-[var(--glow-orange)]"
      >
        <Link to="/" className="flex items-center gap-2 mb-8">
          <div className="grid place-items-center w-9 h-9 rounded-lg bg-gradient-brand text-white shadow-[var(--glow-orange)]">
            <Database className="w-4 h-4" />
          </div>
          <span className="font-bold tracking-wide">DataQ</span>
        </Link>

        <h1 className="text-3xl font-bold tracking-tight">Welcome back</h1>
        <p className="text-sm text-muted-foreground mt-2">Sign in to access your datasets.</p>

        <form onSubmit={onSubmit} className="mt-8 space-y-5">
          <div>
            <label className="text-xs uppercase tracking-widest text-muted-foreground">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-2 w-full rounded-xl bg-secondary/60 border border-border focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none px-4 py-3 text-sm transition"
            />
          </div>
          <div>
            <label className="text-xs uppercase tracking-widest text-muted-foreground">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-2 w-full rounded-xl bg-secondary/60 border border-border focus:border-primary focus:ring-2 focus:ring-primary/30 outline-none px-4 py-3 text-sm transition"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="group relative w-full inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-brand px-6 py-3 text-sm font-semibold text-white shadow-[var(--glow-orange)] transition hover:scale-[1.01] hover:shadow-[var(--glow-red)] disabled:opacity-70"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <>Sign In <ArrowRight className="w-4 h-4" /></>}
          </button>
        </form>

        <p className="text-xs text-muted-foreground mt-6 text-center">
          Demo mode — any credentials will work.
        </p>
      </motion.div>
    </main>
  );
}
