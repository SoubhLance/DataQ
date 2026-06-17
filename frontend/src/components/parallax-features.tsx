import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import {
  ScanSearch,
  AlertTriangle,
  Activity,
  Workflow,
  Sparkles,
  Gauge,
} from "lucide-react";

const features = [
  { icon: ScanSearch, title: "Dataset Profiling", desc: "Detect schema, memory usage, cardinality and feature types." },
  { icon: AlertTriangle, title: "Missing Value Analysis", desc: "Smart imputation suggestions tailored to each column." },
  { icon: Activity, title: "Outlier Detection", desc: "IQR, Z-score and Isolation Forest in one pass." },
  { icon: Workflow, title: "Pipeline Generator", desc: "Generate reusable Python preprocessing scripts." },
  { icon: Sparkles, title: "AI Recommendations", desc: "Receive ML suggestions and model guidance." },
  { icon: Gauge, title: "Quality Score", desc: "Understand dataset readiness at a glance." },
];

export function ParallaxFeatures() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [80, -80]);

  return (
    <section id="features" ref={ref} className="relative py-32 px-6">
      <motion.div style={{ y }} className="pointer-events-none absolute inset-0 grid-bg opacity-50" />
      <div className="relative mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-3">Capabilities</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
            Everything your dataset needs, <span className="text-gradient-brand">before training begins.</span>
          </h2>
        </motion.div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.6, delay: i * 0.08 }}
              className="glass-card glass-card-hover group relative rounded-2xl p-6"
            >
              <div className="grid place-items-center w-12 h-12 rounded-xl bg-gradient-brand text-white shadow-[var(--glow-orange)] mb-5 transition group-hover:scale-110">
                <f.icon className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              <div className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition" style={{ background: "radial-gradient(600px circle at var(--x,50%) var(--y,50%), color-mix(in oklab, var(--brand-orange) 12%, transparent), transparent 40%)" }} />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}