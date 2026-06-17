import apiClient from "./api";
import { PreviewRow } from "@/types/dataset";

export interface ColumnEncodePreviewResponse {
  affected_rows: number;
  sample_before: PreviewRow[];
  sample_after: PreviewRow[];
}

export const columnService = {
  /**
   * Fetch all columns of the dataset.
   */
  getColumns: async (): Promise<string[]> => {
    const response = await apiClient.get<string[]>("/columns/{session_id}");
    return response.data;
  },

  /**
   * Drop selected columns from the dataset.
   */
  dropColumns: async (columns: string[]): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post("/columns/drop", { columns });
    return response.data;
  },

  /**
   * Rename a single column.
   */
  renameColumn: async (old_name: string, new_name: string): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post("/columns/rename", { old_name, new_name });
    return response.data;
  },

  /**
   * Cast a column to a specific type: 'int', 'float', 'string', 'datetime'.
   */
  changeDtype: async (
    column: string,
    new_dtype: "int" | "float" | "string" | "datetime"
  ): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post("/columns/change_dtype", { column, new_dtype });
    return response.data;
  },

  /**
   * Preview label or onehot encoding on a column.
   */
  previewEncoding: async (
    column: string,
    method: "label" | "onehot"
  ): Promise<ColumnEncodePreviewResponse> => {
    const response = await apiClient.post<ColumnEncodePreviewResponse>("/columns/encode/preview", {
      column,
      method,
    });
    return response.data;
  },

  /**
   * Apply label or onehot encoding on a column.
   */
  applyEncoding: async (
    column: string,
    method: "label" | "onehot"
  ): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post("/columns/encode", { column, method });
    return response.data;
  },
};
