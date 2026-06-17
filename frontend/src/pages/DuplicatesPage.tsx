import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { Copy, Trash2, Eye, Undo2, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { AnimatedCounter } from "@/components/dashboard/animated-counter";
import { useSession } from "@/context/SessionContext";
import { duplicateService } from "@/services/duplicateService";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useOperations } from "@/hooks/useOperations";
import { toast } from "sonner";



export default function DuplicatesPage() {
  useEffect(() => {
    document.title = "Duplicates — DataQ";
  }, []);
  const { sessionId, rows, setSession, filename } = useSession();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [keep, setKeep] = useState<"first" | "last" | "none">("first");

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  const duplicatesQuery = useQuery({
    queryKey: ["dataset", "duplicates", sessionId],
    queryFn: () => duplicateService.getDuplicates(),
    enabled: !!sessionId,
  });

  const previewMutation = useMutation({
    mutationKey: ["dataset", "duplicates", "preview", sessionId],
    mutationFn: (keepVal: "first" | "last" | "none") => duplicateService.previewRemoval(keepVal),
  });

  const removeMutation = useMutation({
    mutationFn: (keepVal: "first" | "last" | "none") => duplicateService.removeDuplicates(keepVal),
    onSuccess: (data) => {
      toast.success("Duplicates removed", {
        description: data.message || `Successfully removed duplicates.`,
      });

      // Update session
      if (filename) {
        setSession({
          sessionId: sessionId || "",
          filename,
          rows: data.rows_remaining,
          columns: queryClient.getQueryData<any>(["dataset", "inspect", sessionId])?.shape[1] || 0,
        });
      }

      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ["dataset"] });
      previewMutation.reset();
    },
    onError: (err: any) => {
      toast.error("Cleanup Failed", {
        description: err?.response?.data?.message || err.message || "Failed to remove duplicates.",
      });
    },
  });

  const { undoMutation } = useOperations(sessionId);

  // Trigger preview on load
  useEffect(() => {
    if (sessionId) {
      previewMutation.mutate(keep);
    }
  }, [sessionId, keep]);

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const dupStats = duplicatesQuery.data;
  const isDupLoading = duplicatesQuery.isLoading || previewMutation.isPending;

  const sampleBefore = previewMutation.data?.sample_before || [];
  const sampleAfter = previewMutation.data?.sample_after || [];

  const handleApply = () => {
    removeMutation.mutate(keep);
  };

  const handleUndo = () => {
    undoMutation.mutate();
  };

  return (
    <div>
      <PageHeader
        eyebrow="Cleanup"
        title="Duplicate Rows"
        description="Detect and remove duplicate entries to keep your dataset compact and unbiased."
        actions={
          <div className="flex items-center gap-2">
            <select
              value={keep}
              onChange={(e) => setKeep(e.target.value as any)}
              className="rounded-lg border border-border bg-secondary/60 px-3 py-2 text-xs outline-none focus:border-primary"
            >
              <option value="first">Keep First Occurrence</option>
              <option value="last">Keep Last Occurrence</option>
              <option value="none">Drop All Duplicates</option>
            </select>
            <button
              onClick={handleApply}
              disabled={removeMutation.isPending || !dupStats?.duplicate_rows}
              className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-brand px-3 py-2 text-xs font-semibold text-white shadow-[var(--glow-orange)] hover:scale-[1.02] transition disabled:opacity-50"
            >
              {removeMutation.isPending ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Trash2 className="w-3.5 h-3.5" />
              )}
              Remove Duplicates
            </button>
            <button
              onClick={handleUndo}
              disabled={undoMutation.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs hover:border-primary disabled:opacity-50"
            >
              <Undo2 className="w-3.5 h-3.5" />
              Undo Last Step
            </button>
          </div>
        }
      />

      {isDupLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Scanning dataset for duplicates...</p>
        </div>
      ) : (
        <>
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card rounded-2xl p-5"
            >
              <div className="text-[10px] uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
                <Copy className="w-3 h-3 text-primary" />
                Total Duplicates
              </div>
              <div className="mt-2 text-4xl font-black text-gradient-brand">
                <AnimatedCounter value={dupStats?.duplicate_rows || 0} />
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="glass-card rounded-2xl p-5"
            >
              <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
                Percentage
              </div>
              <div className="mt-2 text-4xl font-black">
                <AnimatedCounter
                  value={dupStats?.duplicate_percent || 0}
                  decimals={2}
                  suffix="%"
                />
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-card rounded-2xl p-5"
            >
              <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
                Rows After Cleanup
              </div>
              <div className="mt-2 text-4xl font-black">
                <AnimatedCounter
                  value={
                    (dupStats?.total_rows || rows || 0) - (dupStats?.duplicate_rows || 0)
                  }
                />
              </div>
            </motion.div>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card rounded-2xl p-6"
            >
              <div className="text-[10px] uppercase tracking-widest text-destructive mb-3">
                Before — Duplicate Rows Detected
              </div>
              {sampleBefore.length === 0 ? (
                <div className="text-center py-12 text-sm text-muted-foreground border border-dashed rounded-xl">
                  No duplicate rows found in dataset.
                </div>
              ) : (
                <RowTable rows={sampleBefore} />
              )}
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card rounded-2xl p-6 border-primary/30 shadow-[var(--glow-orange)]"
            >
              <div className="text-[10px] uppercase tracking-widest text-primary mb-3">
                After — Clean Preview
              </div>
              {sampleAfter.length === 0 ? (
                <div className="text-center py-12 text-sm text-muted-foreground border border-dashed rounded-xl">
                  {dupStats?.duplicate_rows
                    ? "Preview of deduplicated rows"
                    : "Dataset is clean."}
                </div>
              ) : (
                <RowTable rows={sampleAfter} />
              )}
            </motion.div>
          </div>
        </>
      )}
    </div>
  );
}

function RowTable({ rows }: { rows: Record<string, any>[] }) {
  if (rows.length === 0) return null;
  const headers = Object.keys(rows[0]);
  return (
    <div className="overflow-auto rounded-xl border border-border/60 max-h-[400px]">
      <table className="w-full text-xs">
        <thead className="bg-secondary/40 uppercase tracking-widest text-muted-foreground text-[10px] sticky top-0 z-10 backdrop-blur-md">
          <tr>
            {headers.map((k) => (
              <th key={k} className="text-left px-3 py-2 bg-card/60">
                {k}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-border/40 font-mono hover:bg-secondary/25 transition">
              {headers.map((h, j) => (
                <td key={j} className="px-3 py-2 max-w-[120px] truncate" title={String(r[h])}>
                  {r[h] === null || r[h] === undefined ? (
                    <span className="text-destructive italic">NaN</span>
                  ) : (
                    String(r[h])
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}