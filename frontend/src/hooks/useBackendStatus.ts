import { useEffect, useRef, useState, useCallback } from "react";
import apiClient from "@/services/api";

export type BackendStatus = "connecting" | "reachable" | "unavailable";

interface UseBackendStatusOptions {
  /** How often (ms) to re-probe when unavailable/connecting. Default: 7000 */
  retryIntervalMs?: number;
  /**
   * Number of consecutive failures before switching from "connecting" → "unavailable".
   * 0 = stay at "connecting" forever (never show "unavailable"). Default: 5
   */
  failuresBeforeUnavailable?: number;
}

/**
 * Probes GET /  on the backend via the shared axios instance (respects CORS,
 * baseURL, and credentials settings) and retries indefinitely.
 *
 * States:
 *  "connecting"  – First probe or retry in progress, not yet confirmed up or down
 *  "reachable"   – Last probe returned HTTP 2xx
 *  "unavailable" – Probe failed failuresBeforeUnavailable times in a row
 */
export function useBackendStatus(options: UseBackendStatusOptions = {}) {
  const { retryIntervalMs = 7000, failuresBeforeUnavailable = 5 } = options;

  const [status, setStatus] = useState<BackendStatus>("connecting");
  const consecutiveFailures = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const scheduleRetry = (delayMs: number) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(probe, delayMs);
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const probe = useCallback(async () => {
    if (!mountedRef.current) return;

    try {
      // Use the shared apiClient so it goes through the same CORS/baseURL config.
      // GET / is at the root — strip /api/v1 from baseURL to reach it.
      const rootUrl = apiClient.defaults.baseURL?.replace(/\/api\/v1\/?$/, "") ?? "";
      await apiClient.get(rootUrl || "/", {
        baseURL: "", // send request to absolute rootUrl
        timeout: 6000,
        // Don't inject session_id for health probes
        params: {},
      });

      if (!mountedRef.current) return;
      consecutiveFailures.current = 0;
      setStatus("reachable");

      // Re-probe after a longer delay to detect outages
      scheduleRetry(retryIntervalMs * 2);
    } catch {
      if (!mountedRef.current) return;
      consecutiveFailures.current += 1;

      const newStatus: BackendStatus =
        consecutiveFailures.current >= failuresBeforeUnavailable
          ? "unavailable"
          : "connecting";
      setStatus(newStatus);

      // Always retry — never give up
      scheduleRetry(retryIntervalMs);
    }
  }, [retryIntervalMs, failuresBeforeUnavailable]);

  useEffect(() => {
    mountedRef.current = true;
    probe();
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [probe]);

  return { status };
}
