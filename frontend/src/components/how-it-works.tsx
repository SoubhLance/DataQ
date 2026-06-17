import { motion } from "framer-motion";
import { Upload, Search, Sparkles, Code2, BrainCircuit, ChevronRight } from "lucide-react";

const steps = [
  { icon: Upload, label: "Upload Dataset" },
  { icon: Search, label: "Inspect" },
  { icon: Sparkles, label: "Clean" },
  { icon: Code2, label: "Generate Pipeline" },
  { icon: BrainCircuit, label: "Train Models" },
];

export function HowItWorks() {
  return (
    <section id="how" className="relative py-32 px-6 border-t border-border/50">
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="text-center mb-20"
        >
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-3">Workflow</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight">How it works</h2>
        </motion.div>

        <div className="flex flex-col md:flex-row items-center justify-between gap-6 md:gap-2">
          {steps.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.12 }}
              className="flex flex-1 items-center gap-4 md:flex-col md:gap-3"
            >
              <div className="relative">
                <div className="grid place-items-center w-16 h-16 rounded-2xl glass-card text-primary shadow-[var(--glow-orange)]">
                  <s.icon className="w-6 h-6" />
                </div>
                <span className="absolute -top-2 -right-2 grid place-items-center w-6 h-6 rounded-full bg-gradient-brand text-[10px] font-bold text-white">
                  {i + 1}
                </span>
              </div>
              <span className="text-sm font-medium tracking-wide md:text-center">{s.label}</span>
              {i < steps.length - 1 && (
                <ChevronRight className="hidden md:block absolute text-primary opacity-60 md:static" />
              )}
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}