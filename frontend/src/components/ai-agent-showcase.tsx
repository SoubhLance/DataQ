import { motion } from "framer-motion";
import { User, Sparkles, CheckCircle2, Star } from "lucide-react";

export function AIAgentShowcase() {
  return (
    <section id="agent" className="relative py-32 px-6">
      <div className="mx-auto max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="text-center mb-12"
        >
          <p className="text-xs uppercase tracking-[0.3em] text-primary mb-3">AI Agent</p>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight">
            Talk to your <span className="text-gradient-brand">dataset.</span>
          </h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8 }}
          className="glass-card rounded-3xl p-6 md:p-8 space-y-6"
          style={{ boxShadow: "var(--glow-orange), 0 60px 120px -40px var(--brand-red)" }}
        >
          {/* user msg */}
          <div className="flex items-start gap-3 justify-end">
            <div className="rounded-2xl bg-gradient-brand text-white px-4 py-3 max-w-md text-sm shadow-[var(--glow-orange)]">
              Analyze my dataset
            </div>
            <div className="grid place-items-center w-9 h-9 rounded-full bg-secondary text-foreground">
              <User className="w-4 h-4" />
            </div>
          </div>

          {/* ai msg */}
          <div className="flex items-start gap-3">
            <div className="grid place-items-center w-9 h-9 rounded-full bg-gradient-brand text-white shadow-[var(--glow-orange)]">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="flex-1 rounded-2xl border border-primary/30 bg-card/60 backdrop-blur p-5 space-y-5">
              <div>
                <div className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Dataset Health</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-black text-gradient-brand">92</span>
                  <span className="text-muted-foreground">/100</span>
                </div>
              </div>

              <Section title="Problems Found">
                <Item>25 duplicate rows</Item>
                <Item>Missing values in Cholesterol (4.2%)</Item>
                <Item>Moderate class imbalance (70/30)</Item>
              </Section>

              <Section title="Recommendations">
                <li className="text-sm text-muted-foreground">• Median imputation</li>
                <li className="text-sm text-muted-foreground">• StandardScaler</li>
                <li className="text-sm text-muted-foreground">• SMOTE for minority class</li>
              </Section>

              <Section title="Suggested Models">
                <ModelRow name="Random Forest" />
                <ModelRow name="XGBoost" />
                <ModelRow name="Logistic Regression" />
              </Section>

              <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
                <div className="text-xs uppercase tracking-widest text-destructive mb-2">KNN Suggestion</div>
                <pre className="text-xs text-foreground/80 font-mono leading-relaxed">{`k = 5
metric = 'euclidean'
weights = 'uniform'`}</pre>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-widest text-primary mb-2">{title}</div>
      <ul className="space-y-1.5">{children}</ul>
    </div>
  );
}
function Item({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-center gap-2 text-sm text-foreground/80">
      <CheckCircle2 className="w-4 h-4 text-primary" />
      {children}
    </li>
  );
}
function ModelRow({ name }: { name: string }) {
  return (
    <li className="flex items-center gap-2 text-sm text-foreground/80">
      <Star className="w-4 h-4 text-[var(--brand-amber)] fill-[var(--brand-amber)]" />
      {name}
    </li>
  );
}