import { useQuery } from "@tanstack/react-query";
import { inspectService } from "@/services/inspectService";
import { columnService } from "@/services/columnService";

export function useDataset(sessionId: string | null) {
  const inspectQuery = useQuery({
    queryKey: ["dataset", "inspect", sessionId],
    queryFn: () => inspectService.getInspection(),
    enabled: !!sessionId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  const columnsQuery = useQuery({
    queryKey: ["dataset", "columns", sessionId],
    queryFn: () => columnService.getColumns(),
    enabled: !!sessionId,
    staleTime: 5 * 60 * 1000,
  });

  return {
    inspectQuery,
    columnsQuery,
  };
}
