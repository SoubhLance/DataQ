import { Spotlight } from "@/components/ui/spotlight";

export function SpotlightBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <Spotlight className="-top-40 left-0 md:-top-20 md:left-60" fill="oklch(0.72 0.21 45)" />
      <Spotlight className="top-10 right-0 md:top-40 md:right-40" fill="oklch(0.62 0.25 25)" />
    </div>
  );
}