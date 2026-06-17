import { useEffect, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { LoadingScreen } from "@/components/loading-screen";
import { Navbar } from "@/components/navbar";
import { Hero } from "@/components/hero";
import { ParallaxFeatures } from "@/components/parallax-features";
import { HowItWorks } from "@/components/how-it-works";
import { AIAgentShowcase } from "@/components/ai-agent-showcase";
import { BentoGrid } from "@/components/bento-grid";
import { Footer } from "@/components/footer";

export default function LandingPage() {
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    document.title = "DataQ — AI Dataset Quality & Preprocessing Platform";
    const t = setTimeout(() => setLoading(false), 2000);
    return () => clearTimeout(t);
  }, []);

  return (
    <>
      <AnimatePresence>{loading && <LoadingScreen key="loader" />}</AnimatePresence>
      <main className="relative min-h-screen bg-background text-foreground overflow-x-hidden">
        <Navbar />
        <Hero />
        <ParallaxFeatures />
        <HowItWorks />
        <AIAgentShowcase />
        <BentoGrid />
        <Footer />
      </main>
    </>
  );
}
