import { motion } from "framer-motion";
import { Spotlight } from "@/components/ui/spotlight";
import { FloatingParticles } from "@/components/floating-particles";

export function LoadingScreen() {
  return (
    <motion.div
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.8, ease: "easeInOut" }}
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center overflow-hidden bg-black"
    >
      <Spotlight className="-top-20 left-1/4" fill="oklch(0.72 0.21 45)" />
      <Spotlight className="top-20 right-1/4" fill="oklch(0.62 0.25 25)" />
      <FloatingParticles count={30} accent />

      <motion.h1
        initial={{ opacity: 0, y: 20, letterSpacing: "0.5em" }}
        animate={{ opacity: 1, y: 0, letterSpacing: "0.15em" }}
        transition={{ duration: 1.2, ease: [0.2, 0.8, 0.2, 1] }}
        className="text-gradient-brand relative z-10 text-6xl md:text-8xl font-black tracking-widest"
      >
        DATAQ
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6, duration: 0.8 }}
        className="relative z-10 mt-6 text-sm md:text-base text-white/60 tracking-wide"
      >
        Transforming Raw Data Into Intelligence
      </motion.p>

      <div className="relative z-10 mt-10 h-[3px] w-64 overflow-hidden rounded-full bg-white/5">
        <motion.div
          initial={{ width: "0%" }}
          animate={{ width: "100%" }}
          transition={{ duration: 1.8, ease: "easeInOut" }}
          className="h-full bg-gradient-brand"
          style={{ boxShadow: "0 0 20px var(--brand-orange)" }}
        />
      </div>
    </motion.div>
  );
}