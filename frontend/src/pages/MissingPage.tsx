import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { AlertCircle, Eye, Undo2, Loader2, Check } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { useSession } from "@/context/SessionContext";
import { missingService } from "@/services/missingService";
import { visualizationService } from "@/services/visualizationService";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useOperations } from "@/hooks/useOperations";
import { toast } from "sonner";
import { useDataset } from "@/hooks/useDataset";



const sevStyle: Record<string, string> = {
  none: "bg-primary/15 text-primary border-primary/30",
  low: "bg-primary/15 text-primary border-primary/30",
  medium: "bg-accent/15 text-accent border-accent/30",
  high: "bg-destructive/15 text-destructive border-destructive/30",
};

export default function MissingPage() {
  useEffect(() => {
    document.title = "Missing Values — DataQ";
  }, []);
  const { sessionId, setSession, filename } = useSession();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  // Load hooks/services
  const { inspectQuery } = useDataset(sessionId);
  const { undoMutation } = useOperations(sessionId);

  const missingDetailsQuery = useQuery({
    queryKey: ["dataset", "missing", sessionId],
    queryFn: () => missingService.getMissingDetails(),
    enabled: !!sessionId,
  });

  const heatmapQuery = useQuery({
    queryKey: ["dataset", "heatmap", sessionId],
    queryFn: () => visualizationService.getMissingHeatmap(100),
    enabled: !!sessionId,
  });

  // State for selected column and strategy to preview/apply
  const [selectedCol, setSelectedCol] = useState<string | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<"mean" | "median" | "mode" | "constant" | "drop" | null>(null);
  const [constantVal, setConstantVal] = useState<string>("");

  const previewMutation = useMutation({
    mutationFn: ({ column, strategy, val }: { column: string; strategy: any; val?: any }) =>
      missingService.previewImputation(column, strategy, val),
    onSuccess: () => {
      toast.success("Preview loaded");
    },
    onError: (err: any) => {
      toast.error("Preview failed", {
        description: err?.response?.data?.message || err.message,
      });
    },
  });

  const applyMutation = useMutation({
    mutationFn: ({ column, strategy, val }: { column: string; strategy: any; val?: any }) =>
      missingService.applyImputation(column, strategy, val),
    onSuccess: (data) => {
      toast.success("Imputation applied successfully", {
        description: data.message || "Missing values resolved.",
      });

      // Update session rows
      inspectQuery.refetch().then((res) => {
        if (res.data && filename) {
          setSession({
            sessionId: sessionId || "",
            filename,
            rows: res.data.shape[0],
            columns: res.data.shape[1],
          });
        }
      });

      queryClient.invalidateQueries({ queryKey: ["dataset"] });
      // Reset selection
      setSelectedCol(null);
      setSelectedStrategy(null);
      previewMutation.reset();
    },
    onError: (err: any) => {
      toast.error("Imputation failed", {
        description: err?.response?.data?.message || err.message,
      });
    },
  });

  const handlePreview = (column: string, strategy: any, val?: any) => {
    setSelectedCol(column);
    setSelectedStrategy(strategy);
    previewMutation.mutate({ column, strategy, val });
  };

  const handleApply = (column: string, strategy: any, val?: any) => {
    applyMutation.mutate({ column, strategy, val });
  };

  const handleUndo = () => {
    undoMutation.mutate();
  };

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const columnsList = inspectQuery.data?.columns.map((c) => c.name) || [];
  const missingData = missingDetailsQuery.data?.columns || [];
  const heatmapData = heatmapQuery.data || [];

  const isLoading = missingDetailsQuery.isLoading || inspectQuery.isLoading;

  const getSeverity = (percent: number): "none" | "low" | "medium" | "high" => {
    if (percent === 0) return "none";
    if (percent < 5) return "low";
    if (percent < 15) return "medium";
    return "high";
  };

  return (
    <div>
      <PageHeader
        eyebrow="Imputation"
        title="Missing Values"
        description="Visualize gaps and impute with the right strategy per column."
        actions={
          <button
            onClick={handleUndo}
            disabled={undoMutation.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs hover:border-primary disabled:opacity-50"
          >
            <Undo2 className="w-3.5 h-3.5" />
            Undo Last Step
          </button>
        }
      />

      {/* Heatmap Section */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card rounded-2xl p-6 mb-6"
      >
        <div className="text-[10px] uppercase tracking-widest text-primary mb-3">
          Missingness Heatmap
        </div>
        {heatmapQuery.isLoading ? (
          <div className="flex justify-center py-6">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        ) : heatmapData.length === 0 ? (
          <div className="text-center py-6 text-xs text-muted-foreground">
            No heatmap data available.
          </div>
        ) : (
          <div className="overflow-x-auto pb-2">
            <div className="flex flex-col gap-[2px] min-w-max">
              {heatmapData.map((row, rowIndex) => (
                <div key={rowIndex} className="flex gap-[2px]">
                  {columnsList.map((colName) => (
                    <div
                      key={colName}
                      className="w-3 h-3 rounded-sm"
                      style={{
                        background:
                          row[colName] === 1
                            ? "oklch(0.6 0.24 25)" // Red/orange for missing
                            : "rgba(255,255,255,0.08)", // Grey for present
                      }}
                      title={`${colName} row ${rowIndex}: ${row[colName] === 1 ? "Missing" : "Present"}`}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="mt-3 flex items-center gap-3 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm bg-[rgba(255,255,255,0.08)]" />
            Present
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm bg-[oklch(0.6 0.24 25)]" />
            Missing
          </span>
        </div>
      </motion.div>

      {/* Main Table */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Analyzing missing value densities...</p>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-2xl p-6"
        >
          <div className="overflow-x-auto rounded-xl border border-border/60">
            <table className="w-full text-sm">
              <thead className="bg-secondary/40 text-xs uppercase tracking-widest text-muted-foreground">
                <tr>
                  <th className="text-left px-4 py-3">Column</th>
                  <th className="text-left px-4 py-3">Missing Count</th>
                  <th className="text-left px-4 py-3">Missing %</th>
                  <th className="text-left px-4 py-3">Recommendation</th>
                  <th className="text-right px-4 py-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {missingData.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-6 text-muted-foreground">
                      No columns found or dataset is empty.
                    </td>
                  </tr>
                ) : (
                  missingData.map((r) => {
                    const sev = getSeverity(r.percent);
                    return (
                      <tr key={r.column} className="border-t border-border/40 hover:bg-secondary/10 transition">
                        <td className="px-4 py-3 font-medium">{r.column}</td>
                        <td className="px-4 py-3 text-muted-foreground">{r.missing.toLocaleString()}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="flex-1 max-w-[180px] h-1.5 rounded-full bg-secondary overflow-hidden">
                              <div
                                className="h-full bg-gradient-brand"
                                style={{ width: `${Math.min(100, r.percent)}%` }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground tabular-nums">
                              {r.percent}%
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`text-[10px] uppercase tracking-widest border rounded-full px-2 py-0.5 ${sevStyle[sev]}`}
                          >
                            {r.recommended}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          {r.missing > 0 ? (
                            <div className="inline-flex gap-1">
                              {["mean", "median", "mode", "drop"].map((strategy) => (
                                <button
                                  key={strategy}
                                  onClick={() => handlePreview(r.column, strategy as any)}
                                  className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded border border-border hover:border-primary hover:bg-primary/10 transition ${
                                    selectedCol === r.column && selectedStrategy === strategy
                                      ? "bg-primary/20 border-primary text-primary"
                                      : ""
                                  }`}
                                >
                                  {strategy}
                                </button>
                              ))}
                            </div>
                          ) : (
                            <span className="text-xs text-primary flex items-center justify-end gap-1">
                              <Check className="w-3 h-3" /> Clean
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Preview Section */}
      {selectedCol && selectedStrategy && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card rounded-2xl p-6 mt-6 border-primary/30 shadow-[var(--glow-orange)]"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <span className="text-[10px] uppercase tracking-widest text-primary">Previewing Imputation</span>
              <h3 className="text-lg font-bold">
                Column: <span className="text-gradient-brand">{selectedCol}</span> | Strategy:{" "}
                <span className="text-gradient-brand uppercase">{selectedStrategy}</span>
              </h3>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handleApply(selectedCol, selectedStrategy)}
                disabled={applyMutation.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-brand px-4 py-2 text-xs font-semibold text-white shadow-[var(--glow-orange)] hover:scale-[1.02] transition disabled:opacity-50"
              >
                {applyMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Confirm Imputation
              </button>
              <button
                onClick={() => {
                  setSelectedCol(null);
                  setSelectedStrategy(null);
                  previewMutation.reset();
                }}
                className="text-xs px-4 py-2 rounded-lg border border-border hover:border-primary transition"
              >
                Cancel
              </button>
            </div>
          </div>

          {previewMutation.isPending ? (
            <div className="flex justify-center py-10">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="grid lg:grid-cols-2 gap-6">
              <div>
                <div className="text-[10px] uppercase tracking-widest text-destructive mb-2">
                  Before Imputation
                </div>
                <PreviewTable rows={previewMutation.data?.sample_before || []} highlightCol={selectedCol} />
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-widest text-primary mb-2">
                  After Imputation
                </div>
                <PreviewTable rows={previewMutation.data?.sample_after || []} highlightCol={selectedCol} />
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

function PreviewTable({ rows, highlightCol }: { rows: Record<string, any>[]; highlightCol: string }) {
  if (rows.length === 0) {
    return (
      <div className="text-center py-10 text-xs text-muted-foreground border border-dashed rounded-xl">
        No preview rows generated.
      </div>
    );
  }

  const headers = Object.keys(rows[0]);

  return (
    <div className="overflow-auto rounded-xl border border-border/60 max-h-[300px]">
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
              {headers.map((h, j) => {
                const isHighlight = h === highlightCol;
                return (
                  <td
                    key={j}
                    className={`px-3 py-2 max-w-[120px] truncate ${
                      isHighlight ? "bg-primary/10 text-primary font-bold" : ""
                    }`}
                  >
                    {r[h] === null || r[h] === undefined ? (
                      <span className="text-destructive italic">NaN</span>
                    ) : (
                      String(r[h])
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}