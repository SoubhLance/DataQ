import apiClient from "./api";
import { AxiosProgressEvent } from "axios";

export interface UploadResponse {
  session_id: string;
  rows: number;
  columns: number;
  filename: string;
}

export interface AsyncUploadResponse {
  task_id: string;
  session_id: string;
  message: string;
}

export const uploadService = {
  /**
   * Upload dataset file synchronously.
   */
  uploadDataset: async (
    file: File,
    onProgress?: (progressEvent: AxiosProgressEvent) => void
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await apiClient.post<UploadResponse>("/upload?background=false", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      // Override default timeout for potentially large file uploads
      timeout: 120000,
      onUploadProgress: onProgress,
    });
    return response.data;
  },

  /**
   * Upload dataset file in background (async mode) returning a task ID.
   */
  uploadDatasetAsync: async (
    file: File,
    onProgress?: (progressEvent: AxiosProgressEvent) => void
  ): Promise<AsyncUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await apiClient.post<AsyncUploadResponse>("/upload?background=true", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      timeout: 120000,
      onUploadProgress: onProgress,
    });
    return response.data;
  }
};

