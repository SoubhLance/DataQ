import { useMemo } from "react";
import { motion } from "framer-motion";

export function FloatingParticles({ count = 20, accent = false }: { count?: number; accent?: boolean }) {
  const particles = useMemo(
    () =>
      Array.from({ length: count }).map((_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 3 + 1,
        delay: Math.random() * 4,
        dur: 6 + Math.random() * 6,
        red: accent && Math.random() > 0.7,
      })),
    [count, accent],
  );

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {particles.map((p) => (
        <motion.span
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: p.size,
            height: p.size,
            background: p.red ? "var(--brand-red)" : "var(--brand-orange)",
            boxShadow: `0 0 ${p.size * 4}px ${p.red ? "var(--brand-red)" : "var(--brand-orange)"}`,
          }}
          animate={{ y: [0, -40, 0], opacity: [0.2, 1, 0.2] }}
          transition={{ duration: p.dur, delay: p.delay, repeat: Infinity, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}