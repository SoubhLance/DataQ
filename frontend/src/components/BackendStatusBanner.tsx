import { motion, AnimatePresence } from "framer-motion";
import { Wifi, WifiOff, Loader2 } from "lucide-react";
import { useBackendStatus } from "@/hooks/useBackendStatus";
import { API_BASE_URL } from "@/services/api";

/**
 * Renders a slim status banner at the top of the viewport.
 * Shows nothing when the backend is reachable.
 */
export function BackendStatusBanner() {
  const { status } = useBackendStatus({ retryIntervalMs: 8000 });

  const show = status !== "reachable";

  const config = {
    connecting: {
      bg: "bg-amber-500/10 border-amber-500/30 text-amber-400",
      icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
      message: "Connecting to backend…",
    },
    unavailable: {
      bg: "bg-destructive/10 border-destructive/30 text-destructive",
      icon: <WifiOff className="w-3.5 h-3.5" />,
      message: `Backend unavailable at ${API_BASE_URL.replace("/api/v1", "")}`,
    },
    reachable: {
      bg: "",
      icon: <Wifi className="w-3.5 h-3.5" />,
      message: "",
    },
  } as const;

  const current = config[status];

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="backend-status"
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.25 }}
          className={`fixed top-0 inset-x-0 z-[100] flex items-center justify-center gap-2 border-b px-4 py-2 text-xs font-medium ${current.bg}`}
        >
          {current.icon}
          <span>{current.message}</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
