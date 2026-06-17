import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { pipelineService } from "@/services/pipelineService";
import { toast } from "sonner";
import { useSession } from "@/context/SessionContext";

export function useOperations(sessionId: string | null) {
  const queryClient = useQueryClient();
  const { setSession, filename } = useSession();

  const operationsQuery = useQuery({
    queryKey: ["dataset", "operations", sessionId],
    queryFn: () => pipelineService.getOperationsHistory(),
    enabled: !!sessionId,
  });

  const undoMutation = useMutation({
    mutationFn: () => pipelineService.undoLastStep(),
    onSuccess: (data) => {
      toast.success("Last operation reverted", {
        description: data.message || "Successfully undone.",
      });

      // Update SessionContext state if needed (rows & columns)
      if (filename) {
        setSession({
          sessionId: sessionId || "",
          filename: filename,
          rows: data.rows,
          columns: data.columns,
        });
      }

      // Invalidate all dataset-related queries in React Query cache
      queryClient.invalidateQueries({ queryKey: ["dataset"] });
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.message || error?.message || "Could not undo last operation.";
      toast.error("Undo Failed", {
        description: msg,
      });
    },
  });

  return {
    operationsQuery,
    undoMutation,
  };
}
