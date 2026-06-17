import { motion } from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import { Link } from "react-router-dom";
import { SpotlightBackground } from "@/components/spotlight-demo";
import { FloatingParticles } from "@/components/floating-particles";

export function Hero() {
  return (
    <section className="relative isolate flex min-h-[100svh] w-full items-center justify-center overflow-hidden bg-background pt-24">
      <SpotlightBackground />
      <div className="absolute inset-0 grid-bg" />
      <FloatingParticles count={24} accent />

      <div className="relative z-10 mx-auto max-w-5xl px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/5 px-4 py-1.5 text-xs uppercase tracking-[0.2em] text-primary"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-primary shadow-[0_0_10px_var(--brand-orange)]" />
          AI Dataset Intelligence
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.1, ease: [0.2, 0.8, 0.2, 1] }}
          className="mt-8 text-balance text-5xl md:text-7xl font-black leading-[0.95] tracking-tight"
        >
          Transform Raw Data Into{" "}
          <span className="text-gradient-brand">ML-Ready Intelligence</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.25 }}
          className="mx-auto mt-7 max-w-2xl text-base md:text-lg text-muted-foreground leading-relaxed"
        >
          Analyze datasets, discover problems, clean data, generate pipelines, and receive
          AI-powered machine learning recommendations.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.4 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <Link
            to="/login"
            className="group relative inline-flex items-center gap-2 rounded-xl bg-gradient-brand px-6 py-3 text-sm font-semibold text-white shadow-[var(--glow-orange)] transition hover:scale-[1.03] hover:shadow-[var(--glow-red)]"
          >
            Get Started
            <ArrowRight className="w-4 h-4 transition group-hover:translate-x-0.5" />
          </Link>
          <a
            href="#agent"
            className="glass-card glass-card-hover inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-medium"
          >
            <Play className="w-4 h-4 text-primary" />
            View Demo
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 1 }}
          className="mt-16 flex items-center justify-center gap-8 text-xs text-muted-foreground"
        >
          {["Profiling", "Imputation", "Outliers", "Pipelines", "ML Suggest"].map((t) => (
            <span key={t} className="hidden md:inline tracking-widest uppercase">
              {t}
            </span>
          ))}
        </motion.div>
      </div>
    </section>
  );
}