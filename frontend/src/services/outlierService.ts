import apiClient from "./api";
import { OutlierCheckResponse, PreviewResponse } from "@/types/dataset";

export const outlierService = {
  /**
   * Scan dataset for outliers using IQR, Z-Score, or Isolation Forest.
   */
  getOutliers: async (
    method: "iqr" | "zscore" | "iforest" = "iqr",
    threshold: number = 3.0,
    contamination: number = 0.05
  ): Promise<OutlierCheckResponse> => {
    const response = await apiClient.get<OutlierCheckResponse>("/outliers/{session_id}", {
      params: { method, threshold, contamination },
    });
    return response.data;
  },

  /**
   * Preview rows modified by outlier removal or capping.
   */
  previewTreatment: async (
    column: string,
    method: "iqr" | "zscore" | "iforest",
    action: "remove" | "cap" | "keep",
    threshold: number = 3.0,
    contamination: number = 0.05
  ): Promise<PreviewResponse> => {
    const response = await apiClient.post<PreviewResponse>("/outliers/preview", {
      column,
      method,
      action,
      threshold,
      contamination,
    });
    return response.data;
  },

  /**
   * Treat outliers in a column. Supports synchronous or async background tasks.
   */
  applyTreatment: async (
    column: string,
    method: "iqr" | "zscore" | "iforest",
    action: "remove" | "cap" | "keep",
    threshold: number = 3.0,
    contamination: number = 0.05,
    background: boolean = false
  ): Promise<{ status?: string; message: string; task_id?: string }> => {
    const response = await apiClient.post(
      "/outliers/remove",
      {
        column,
        method,
        action,
        threshold,
        contamination,
      },
      {
        params: { background },
      }
    );
    return response.data;
  }
};
