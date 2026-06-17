import axios from "axios";
import { toast } from "sonner";

// ── Environment-driven URLs ──────────────────────────────────────────────────
// Set these in frontend/.env:
//   VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
//   VITE_WS_BASE_URL=ws://127.0.0.1:8000/api/v1
const _apiBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
const _wsBase  = import.meta.env.VITE_WS_BASE_URL  as string | undefined;

if (!_apiBase) {
  console.warn(
    "[DataQ] VITE_API_BASE_URL is not set. " +
    "Create frontend/.env with VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1"
  );
}

export const API_BASE_URL: string = _apiBase ?? "http://127.0.0.1:8000/api/v1";
export const WS_BASE_URL:  string = _wsBase  ?? "ws://127.0.0.1:8000/api/v1";

// ── Axios instance ───────────────────────────────────────────────────────────
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ── Request Interceptor: inject sessionId automatically ──────────────────────
apiClient.interceptors.request.use(
  (config) => {
    const sessionId = localStorage.getItem("session_id");

    // Only inject if we actually have a session ID
    if (sessionId) {
      // 1. Replace {session_id} path placeholder if present
      if (config.url && config.url.includes("{session_id}")) {
        config.url = config.url.replace("{session_id}", sessionId);
      }

      // 2. Inject into query params (but don't override explicit params)
      if (!config.params?.session_id) {
        config.params = {
          ...config.params,
          session_id: sessionId,
        };
      }

      // 3. Inject into JSON body only — skip FormData (multipart uploads)
      if (
        config.data &&
        typeof config.data === "object" &&
        !(config.data instanceof FormData) &&
        !config.data.session_id
      ) {
        config.data = { ...config.data, session_id: sessionId };
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// ── Response Interceptor: centralised error handling ─────────────────────────
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.message || error.message || "An unexpected error occurred.";
    const detail = error.response?.data?.detail;

    console.error("[DataQ API Error]", error);

    if (detail === "SESSION_NOT_FOUND" || detail === "SESSION_EXPIRED") {
      toast.error("Session Expired", {
        description:
          "Your cleaning session has expired or is invalid. Please upload your dataset again.",
      });
      localStorage.removeItem("session_id");
      localStorage.removeItem("session_filename");
      localStorage.removeItem("session_rows");
      localStorage.removeItem("session_columns");

      if (window.location.pathname !== "/dashboard/upload") {
        window.location.href = "/dashboard/upload";
      }
    } else if (error.code === "ERR_NETWORK" || error.code === "ECONNREFUSED") {
      // Don't toast here — useBackendStatus hook handles global connectivity UX.
      // Only log so caller can decide what to show.
      console.warn("[DataQ] Network error — backend may be unreachable at", API_BASE_URL);
    } else if (error.response?.status === 413 || detail === "FILE_TOO_LARGE") {
      toast.error("File Too Large", { description: message });
    } else if (detail === "COLUMN_NOT_FOUND") {
      toast.error("Column Error", { description: message });
    } else if (error.response) {
      // A real HTTP error response (4xx / 5xx other than the above)
      toast.error("Operation Failed", { description: message });
    }
    // If error.code === "ERR_NETWORK" we intentionally stay silent here;
    // the BackendStatus component shows the connectivity banner instead.

    return Promise.reject(error);
  }
);

export default apiClient;
