import apiClient from "./api";
import { InspectResponse, QualityResponse, CorrelationResponse, ImbalanceResponse } from "@/types/dataset";

export const inspectService = {
  /**
   * Fetch basic structural metadata of the dataset (shape, columns, memory, types).
   */
  getInspection: async (): Promise<InspectResponse> => {
    const response = await apiClient.get<InspectResponse>("/inspect/{session_id}");
    return response.data;
  },

  /**
   * Fetch overall dataset quality score and warnings.
   */
  getQualityScore: async (): Promise<QualityResponse> => {
    const response = await apiClient.get<QualityResponse>("/quality/{session_id}");
    return response.data;
  },

  /**
   * Fetch Pearson correlation matrix and recommendations for highly correlated column pairs.
   */
  getCorrelationMatrix: async (threshold: number = 0.9): Promise<CorrelationResponse> => {
    const response = await apiClient.get<CorrelationResponse>("/correlation/{session_id}", {
      params: { threshold },
    });
    return response.data;
  },

  /**
   * Fetch class distribution and imbalance diagnostics for a target classification column.
   */
  getClassImbalance: async (target: string): Promise<ImbalanceResponse> => {
    const response = await apiClient.get<ImbalanceResponse>("/imbalance/{session_id}", {
      params: { target },
    });
    return response.data;
  },

  /**
   * Fetch a sample of raw rows from the dataset.
   */
  getDataframeSample: async (limit = 20): Promise<Record<string, any>[]> => {
    const response = await apiClient.get<Record<string, any>[]>("/sample/{session_id}", {
      params: { limit },
    });
    return response.data;
  }
};

