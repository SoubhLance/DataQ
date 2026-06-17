import apiClient, { WS_BASE_URL } from "./api";
import { Task } from "@/types/operation";

export const taskService = {
  /**
   * Fetch the current status, progress, and results of a background task.
   */
  getTaskStatus: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get<Task>(`/tasks/${taskId}`);
    return response.data;
  },

  /**
   * Opens a WebSocket connection for session progress and task updates.
   */
  connectSessionWebSocket: (
    sessionId: string,
    onMessage: (payload: any) => void,
    onError?: (error: Event) => void
  ): WebSocket => {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/session/${sessionId}`);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        onMessage(payload);
      } catch (e) {
        console.error("WebSocket message parse error:", e);
      }
    };

    if (onError) {
      ws.onerror = onError;
    }

    return ws;
  },
};
