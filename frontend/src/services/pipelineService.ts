import apiClient from "./api";
import { Operation } from "@/types/operation";

export interface PipelineResponse {
  format: string;
  content_type: string;
  pipeline: string;
}

export interface UndoResponse {
  status: string;
  message: string;
  operations_remaining: number;
  rows: number;
  columns: number;
}

export const pipelineService = {
  /**
   * Fetch generated code or recipe for the current transformation pipeline.
   */
  getPipelineCode: async (
    format: "pandas" | "sklearn" | "notebook" | "yaml"
  ): Promise<PipelineResponse> => {
    const response = await apiClient.get<PipelineResponse>(`/pipeline/{session_id}`, {
      params: { format },
    });
    return response.data;
  },

  /**
   * Undo the last preprocessing step.
   */
  undoLastStep: async (): Promise<UndoResponse> => {
    const response = await apiClient.post<UndoResponse>(`/undo/{session_id}`);
    return response.data;
  },

  /**
   * Retrieve the list of operations applied to the dataset in this session.
   */
  getOperationsHistory: async (): Promise<Operation[]> => {
    const response = await apiClient.get<Operation[]>(`/operations/{session_id}`);
    return response.data;
  },
};
