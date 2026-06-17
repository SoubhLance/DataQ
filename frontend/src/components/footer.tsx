import { Database } from "lucide-react";

export function Footer() {
  return (
    <footer className="relative bg-black text-white/70 py-16 px-6 mt-10">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--brand-orange)] to-transparent" />
      <div className="mx-auto max-w-6xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2">
          <div className="grid place-items-center w-8 h-8 rounded-lg bg-gradient-brand text-white">
            <Database className="w-4 h-4" />
          </div>
          <span className="font-bold tracking-wide text-white">DataQ</span>
        </div>
        <p className="text-sm text-center">
          Built for Data Scientists, ML Engineers, and Curious Minds.
        </p>
        <p className="text-xs text-white/40">© {new Date().getFullYear()} DataQ</p>
      </div>
    </footer>
  );
}