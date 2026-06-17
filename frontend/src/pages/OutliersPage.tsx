import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { AlertCircle, ScatterChart as ScatterIcon, Eye, Undo2, Loader2, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { AnimatedCounter } from "@/components/dashboard/animated-counter";
import { useSession } from "@/context/SessionContext";
import { outlierService } from "@/services/outlierService";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useDataset } from "@/hooks/useDataset";
import { useOperations } from "@/hooks/useOperations";
import { toast } from "sonner";



export default function OutliersPage() {
  useEffect(() => {
    document.title = "Outliers — DataQ";
  }, []);
  const { sessionId, setSession, filename } = useSession();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  const { inspectQuery } = useDataset(sessionId);
  const { undoMutation } = useOperations(sessionId);

  const numericColumns = inspectQuery.data?.numeric_columns || [];
  const [selectedCol, setSelectedCol] = useState<string>("");
  const [selectedMethod, setSelectedMethod] = useState<"iqr" | "zscore" | "iforest">("iqr");
  const [selectedAction, setSelectedAction] = useState<"remove" | "cap">("remove");

  useEffect(() => {
    if (numericColumns.length > 0 && !selectedCol) {
      setSelectedCol(numericColumns[0]);
    }
  }, [numericColumns, selectedCol]);

  // Run outlier scans for top statistics
  const iqrQuery = useQuery({
    queryKey: ["dataset", "outliers", "iqr", sessionId],
    queryFn: () => outlierService.getOutliers("iqr"),
    enabled: !!sessionId,
  });

  const zscoreQuery = useQuery({
    queryKey: ["dataset", "outliers", "zscore", sessionId],
    queryFn: () => outlierService.getOutliers("zscore"),
    enabled: !!sessionId,
  });

  const iforestQuery = useQuery({
    queryKey: ["dataset", "outliers", "iforest", sessionId],
    queryFn: () => outlierService.getOutliers("iforest"),
    enabled: !!sessionId,
  });

  const previewMutation = useMutation({
    mutationFn: () =>
      outlierService.previewTreatment(selectedCol, selectedMethod, selectedAction),
    onSuccess: () => {
      toast.success("Outlier preview loaded");
    },
    onError: (err: any) => {
      toast.error("Preview failed", {
        description: err?.response?.data?.message || err.message,
      });
    },
  });

  const applyMutation = useMutation({
    mutationFn: () =>
      outlierService.applyTreatment(selectedCol, selectedMethod, selectedAction, 3.0, 0.05, false),
    onSuccess: (data) => {
      toast.success("Outlier treatment applied", {
        description: data.message || "Successfully treated outliers.",
      });

      // Update session shape
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
      previewMutation.reset();
    },
    onError: (err: any) => {
      toast.error("Failed to apply outlier treatment", {
        description: err?.response?.data?.message || err.message,
      });
    },
  });

  // Automatically trigger preview when variables change
  useEffect(() => {
    if (sessionId && selectedCol && selectedMethod && selectedAction) {
      previewMutation.mutate();
    }
  }, [sessionId, selectedCol, selectedMethod, selectedAction]);

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const iqrTotal = iqrQuery.data?.columns.reduce((sum, c) => sum + c.outliers, 0) || 0;
  const zscoreTotal = zscoreQuery.data?.columns.reduce((sum, c) => sum + c.outliers, 0) || 0;
  const iforestTotal = iforestQuery.data?.columns.reduce((sum, c) => sum + c.outliers, 0) || 0;

  const currentColumnDetails =
    selectedMethod === "iqr"
      ? iqrQuery.data?.columns.find((c) => c.column === selectedCol)
      : selectedMethod === "zscore"
        ? zscoreQuery.data?.columns.find((c) => c.column === selectedCol)
        : iforestQuery.data?.columns.find((c) => c.column === selectedCol);

  const sampleBefore = previewMutation.data?.sample_before || [];
  const sampleAfter = previewMutation.data?.sample_after || [];

  return (
    <div>
      <PageHeader
        eyebrow="Anomaly"
        title="Outlier Detection"
        description="Detect, cap, or drop anomalous samples using statistical and ML-based methods."
        actions={
          <button
            onClick={() => undoMutation.mutate()}
            disabled={undoMutation.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-xs hover:border-primary disabled:opacity-50"
          >
            <Undo2 className="w-3.5 h-3.5" />
            Undo Last Step
          </button>
        }
      />

      {/* Top Cards showing comparison of methods */}
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        {[
          { name: "IQR (Tukey Fences)", count: iqrTotal, query: iqrQuery },
          { name: "Z-Score (Standard deviation)", count: zscoreTotal, query: zscoreQuery },
          { name: "Isolation Forest (ML-based)", count: iforestTotal, query: iforestQuery },
        ].map((m, i) => (
          <motion.div
            key={m.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`glass-card rounded-2xl p-5 border-border/60 ${
              selectedMethod === (i === 0 ? "iqr" : i === 1 ? "zscore" : "iforest")
                ? "border-primary/40 shadow-[var(--glow-orange)]"
                : ""
            }`}
          >
            <div className="text-[10px] uppercase tracking-widest text-primary">{m.name}</div>
            {m.query.isLoading ? (
              <div className="h-9 flex items-center mt-2">
                <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="mt-2 text-4xl font-black text-gradient-brand">
                <AnimatedCounter value={m.count} />
              </div>
            )}
            <div className="text-xs text-muted-foreground mt-1">Outliers detected across numeric columns</div>
          </motion.div>
        ))}
      </div>

      {/* Configuration Controls */}
      <div className="glass-card rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">
            Select Numeric Column
          </label>
          <select
            value={selectedCol}
            onChange={(e) => setSelectedCol(e.target.value)}
            className="rounded-lg border border-border bg-secondary/60 px-3 py-2 text-xs outline-none focus:border-primary min-w-[150px]"
          >
            {numericColumns.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">
            Detection Method
          </label>
          <select
            value={selectedMethod}
            onChange={(e) => setSelectedMethod(e.target.value as any)}
            className="rounded-lg border border-border bg-secondary/60 px-3 py-2 text-xs outline-none focus:border-primary"
          >
            <option value="iqr">IQR (1.5 × IQR)</option>
            <option value="zscore">Z-Score (|z| &gt; 3.0)</option>
            <option value="iforest">Isolation Forest (contamination=0.05)</option>
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">
            Treatment Action
          </label>
          <select
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value as any)}
            className="rounded-lg border border-border bg-secondary/60 px-3 py-2 text-xs outline-none focus:border-primary"
          >
            <option value="remove">Remove Outlier Rows</option>
            <option value="cap">Cap to Boundaries</option>
          </select>
        </div>

        <div className="ml-auto mt-auto">
          <button
            onClick={() => applyMutation.mutate()}
            disabled={applyMutation.isPending || !currentColumnDetails?.outliers}
            className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-brand px-4 py-2.5 text-xs font-semibold text-white shadow-[var(--glow-orange)] hover:opacity-90 transition disabled:opacity-50"
          >
            {applyMutation.isPending ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Trash2 className="w-3.5 h-3.5" />
            )}
            Apply Outlier Treatment
          </button>
        </div>
      </div>

      {/* Preview Section */}
      <div className="grid lg:grid-cols-[1.2fr_1fr] gap-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-[10px] uppercase tracking-widest text-primary">Column Profile</p>
              <h3 className="font-semibold">{selectedCol || "No Column Selected"}</h3>
            </div>
            <div className="text-right">
              <div className="text-sm font-bold text-destructive">
                {currentColumnDetails?.outliers || 0} outliers ({currentColumnDetails?.percentage || 0}%)
              </div>
              {currentColumnDetails?.lower_bound !== undefined && (
                <div className="text-[10px] text-muted-foreground mt-0.5">
                  Bounds: [{currentColumnDetails.lower_bound.toFixed(2)}, {currentColumnDetails.upper_bound?.toFixed(2)}]
                </div>
              )}
            </div>
          </div>

          <div className="text-sm border border-dashed rounded-xl p-8 text-center text-muted-foreground flex flex-col items-center justify-center min-h-[200px]">
            <ScatterIcon className="w-8 h-8 text-primary/40 mb-2" />
            <span className="font-semibold text-foreground">Treatment Preview Data</span>
            <span className="text-xs mt-1">
              Select variables to preview outliers. Before and After tables are displayed on the right pane.
            </span>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-card rounded-2xl p-6"
        >
          <div className="text-[10px] uppercase tracking-widest text-primary mb-3">
            Preview: Outlier Rows
          </div>
          {previewMutation.isPending ? (
            <div className="flex justify-center py-10">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : sampleBefore.length === 0 ? (
            <div className="text-center py-12 text-sm text-muted-foreground border border-dashed rounded-xl">
              No outliers found in {selectedCol} using {selectedMethod}.
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="text-[10px] uppercase tracking-widest text-destructive mb-1">
                  Before Treatment
                </div>
                <PreviewRows rows={sampleBefore} highlightCol={selectedCol} />
              </div>
              {selectedAction === "cap" && (
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-primary mb-1">
                    After Treatment (Capped)
                  </div>
                  <PreviewRows rows={sampleAfter} highlightCol={selectedCol} />
                </div>
              )}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

function PreviewRows({ rows, highlightCol }: { rows: Record<string, any>[]; highlightCol: string }) {
  if (rows.length === 0) return null;
  return (
    <div className="overflow-auto rounded-xl border border-border/60 max-h-[180px]">
      <table className="w-full text-xs">
        <thead className="bg-secondary/40 text-[10px] uppercase tracking-widest text-muted-foreground sticky top-0 z-10 backdrop-blur-md">
          <tr>
            <th className="text-left px-3 py-1.5 bg-card/60">Row #</th>
            <th className="text-left px-3 py-1.5 bg-card/60">{highlightCol}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-border/40 font-mono hover:bg-secondary/20 transition">
              <td className="px-3 py-1 text-muted-foreground">#{i + 1}</td>
              <td className="px-3 py-1 font-bold text-destructive">
                {r[highlightCol] === null ? "NaN" : String(r[highlightCol])}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}