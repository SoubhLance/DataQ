import apiClient from "./api";
import { PreviewRow } from "@/types/dataset";

export interface ScalingPreviewResponse {
  affected_rows: number;
  sample_before: PreviewRow[];
  sample_after: PreviewRow[];
}

export const scalingService = {
  /**
   * Preview the result of scaling on selected numeric columns.
   */
  previewScaling: async (
    columns: string[],
    method: "standard" | "minmax" | "robust"
  ): Promise<ScalingPreviewResponse> => {
    const response = await apiClient.post<ScalingPreviewResponse>("/scaling/preview", {
      columns,
      method,
    });
    return response.data;
  },

  /**
   * Apply scaling to the selected numeric columns in the dataset.
   */
  applyScaling: async (
    columns: string[],
    method: "standard" | "minmax" | "robust"
  ): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post("/scaling/apply", {
      columns,
      method,
    });
    return response.data;
  },
};
