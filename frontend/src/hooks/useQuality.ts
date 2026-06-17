import { useQuery } from "@tanstack/react-query";
import { inspectService } from "@/services/inspectService";

export function useQuality(sessionId: string | null) {
  const qualityQuery = useQuery({
    queryKey: ["dataset", "quality", sessionId],
    queryFn: () => inspectService.getQualityScore(),
    enabled: !!sessionId,
    staleTime: 2 * 60 * 1000, // Cache for 2 minutes
  });

  return {
    qualityQuery,
  };
}
