import apiClient, { API_BASE_URL } from "./api";
import { ReportResponse } from "@/types/report";

export const reportService = {
  /**
   * Generate the dataset quality check metadata report.
   */
  generateJsonReport: async (
    background = false
  ): Promise<ReportResponse | { task_id: string; message: string }> => {
    const response = await apiClient.post<ReportResponse | { task_id: string; message: string }>(
      "/export/json-report",
      {},
      {
        params: {
          background,
        },
      }
    );
    return response.data;
  },

  /**
   * Get the download URL directly for external usage if needed.
   */
  getCleanedFileUrl: (sessionId: string, format: "csv" | "xlsx" | "json" | "parquet"): string => {
    return `${API_BASE_URL}/export/file/${sessionId}?format=${format}`;
  },

  /**
   * Download the cleaned version of the dataset using standard file download triggers.
   */
  downloadCleanedFile: async (
    format: "csv" | "xlsx" | "json" | "parquet",
    filename: string
  ): Promise<void> => {
    const response = await apiClient.post(
      `/export/file/{session_id}`,
      {},
      {
        params: { format },
        responseType: "blob",
      }
    );

    const blob = new Blob([response.data], { type: response.headers["content-type"] });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    
    const baseName = filename ? filename.substring(0, filename.lastIndexOf(".")) || filename : "dataset";
    link.setAttribute("download", `cleaned_${baseName}.${format}`);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
