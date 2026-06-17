import apiClient from "./api";
import { DuplicateDetectResponse, DuplicatePreviewResponse } from "@/types/duplicate_schema"; // Wait, we can import from types/dataset or custom schemas

// Let's import from our centralized types/dataset.ts instead
import { PreviewResponse } from "@/types/dataset";

export interface DuplicateDetectResponse {
  total_rows: number;
  duplicate_rows: number;
  duplicate_percent: number;
}

export const duplicateService = {
  /**
   * Fetch duplicate row counts and statistics.
   */
  getDuplicates: async (): Promise<DuplicateDetectResponse> => {
    const response = await apiClient.get<DuplicateDetectResponse>("/duplicates/{session_id}");
    return response.data;
  },

  /**
   * Preview rows affected by deduplication.
   */
  previewRemoval: async (keep: "first" | "last" | "none"): Promise<PreviewResponse> => {
    const response = await apiClient.post<PreviewResponse>("/duplicates/preview", { keep });
    return response.data;
  },

  /**
   * Apply duplicate rows removal in-place.
   */
  removeDuplicates: async (keep: "first" | "last" | "none"): Promise<{ status: string; message: string; rows_remaining: number }> => {
    const response = await apiClient.post("/duplicates/remove", { keep });
    return response.data;
  }
};
