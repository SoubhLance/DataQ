import apiClient from "./api";

export interface MissingHeatmapRow {
  [key: string]: number; // 0 for present, 1 for missing
}

export interface CorrelationHeatmapCell {
  x: string;
  y: string;
  value: number | null;
}

export interface DistributionBin {
  bin_start: number;
  bin_end: number;
  count: number;
}

export interface BoxplotStats {
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  lower_whisker: number;
  upper_whisker: number;
  outliers: number[];
}

export const visualizationService = {
  /**
   * Fetch missingness matrix data for heatmap visualization.
   */
  getMissingHeatmap: async (maxRows = 150): Promise<MissingHeatmapRow[]> => {
    const response = await apiClient.get<MissingHeatmapRow[]>("/visualization/missing/{session_id}", {
      params: { max_rows: maxRows },
    });
    return response.data;
  },

  /**
   * Fetch Pearson correlation coefficients in a flat coordinate layout.
   */
  getCorrelationHeatmap: async (): Promise<CorrelationHeatmapCell[]> => {
    const response = await apiClient.get<CorrelationHeatmapCell[]>("/visualization/correlation/{session_id}");
    return response.data;
  },

  /**
   * Fetch histogram bin frequencies for a numeric column.
   */
  getColumnDistribution: async (column: string, bins = 10): Promise<DistributionBin[]> => {
    const response = await apiClient.get<DistributionBin[]>("/visualization/distribution/{session_id}", {
      params: { column, bins },
    });
    return response.data;
  },

  /**
   * Fetch boxplot summary statistics (quartiles, whiskers, outliers) for a column.
   */
  getColumnBoxplot: async (column: string): Promise<BoxplotStats> => {
    const response = await apiClient.get<BoxplotStats>("/visualization/boxplot/{session_id}", {
      params: { column },
    });
    return response.data;
  },
};
