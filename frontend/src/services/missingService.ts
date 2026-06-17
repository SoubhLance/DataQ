import apiClient from "./api";
import { MissingCheckResponse, PreviewResponse } from "@/types/dataset";

export const missingService = {
  /**
   * Fetch missing value statistics and recommended imputation strategies.
   */
  getMissingDetails: async (): Promise<MissingCheckResponse> => {
    const response = await apiClient.get<MissingCheckResponse>("/missing/{session_id}");
    return response.data;
  },

  /**
   * Preview imputation changes before applying them.
   */
  previewImputation: async (
    column: string,
    strategy: "mean" | "median" | "mode" | "constant" | "drop",
    constantValue?: any
  ): Promise<PreviewResponse> => {
    const response = await apiClient.post<PreviewResponse>("/missing/preview", {
      column,
      strategy,
      constant_value: constantValue,
    });
    return response.data;
  },

  /**
   * Apply imputation strategy to a column.
   */
  applyImputation: async (
    column: string,
    strategy: "mean" | "median" | "mode" | "constant" | "drop",
    constantValue?: any
  ): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post("/missing/apply", {
      column,
      strategy,
      constant_value: constantValue,
    });
    return response.data;
  }
};
