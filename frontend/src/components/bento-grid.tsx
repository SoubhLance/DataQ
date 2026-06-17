import { motion } from "framer-motion";
import {
  Database, Copy, AlertCircle, Activity, Tag, Ruler,
  GitCompare, Gauge, FileDown, Code, Bot, Brain,
} from "lucide-react";

const items = [
  { icon: Database, title: "Dataset Profiling", span: "md:col-span-2" },
  { icon: Copy, title: "Duplicate Detection" },
  { icon: AlertCircle, title: "Missing Values" },
  { icon: Activity, title: "Outlier Detection" },
  { icon: Tag, title: "Encoding" },
  { icon: Ruler, title: "Scaling" },
  { icon: GitCompare, title: "Correlation Analysis", span: "md:col-span-2" },
  { icon: Gauge, title: "Quality Score" },
  { icon: FileDown, title: "Export CSV" },
  { icon: Code, title: "Python Code Generator" },
  { icon: Bot, title: "AI Assistant" },
  { icon: Brain, title: "ML Recommendations" },
];

export function BentoGrid() {
  return (
    <section id="grid" className="relative py-32 px-6 border-t border-border/50">
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-3">Full Toolkit</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
            Twelve modules. <span className="text-gradient-brand">One workflow.</span>
          </h2>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {items.map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className={`glass-card glass-card-hover group relative rounded-2xl p-5 min-h-[140px] flex flex-col justify-between overflow-hidden ${item.span ?? ""}`}
            >
              <item.icon className="w-6 h-6 text-primary transition group-hover:scale-110" />
              <div>
                <h3 className="text-sm md:text-base font-semibold">{item.title}</h3>
              </div>
              <div className="pointer-events-none absolute -bottom-10 -right-10 w-32 h-32 rounded-full bg-gradient-brand opacity-0 blur-3xl transition group-hover:opacity-40" />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}