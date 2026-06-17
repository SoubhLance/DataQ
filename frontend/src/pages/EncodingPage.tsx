import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect, useMemo } from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { useSession } from "@/context/SessionContext";
import { useDataset } from "@/hooks/useDataset";
import { columnService } from "@/services/columnService";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useOperations } from "@/hooks/useOperations";
import { Loader2, Check, Tags, Undo2 } from "lucide-react";
import { toast } from "sonner";



export default function EncodingPage() {
  useEffect(() => {
    document.title = "Encoding — DataQ";
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

  const categoricalColumns = useMemo(() => {
    if (!inspectQuery.data) return [];
    const cats = inspectQuery.data.categorical_columns || [];
    return inspectQuery.data.columns.filter((c) => cats.includes(c.name));
  }, [inspectQuery.data]);

  const [selectedCol, setSelectedCol] = useState<string>("");
  const [method, setMethod] = useState<"label" | "onehot">("onehot");

  useEffect(() => {
    if (categoricalColumns.length > 0 && !selectedCol) {
      setSelectedCol(categoricalColumns[0].name);
    }
  }, [categoricalColumns, selectedCol]);

  const previewMutation = useMutation({
    mutationFn: () => columnService.previewEncoding(selectedCol, method),
    onError: (err: any) => {
      toast.error("Preview failed", {
        description: err?.response?.data?.message || err.message,
      });
    },
  });

  const applyMutation = useMutation({
    mutationFn: () => columnService.applyEncoding(selectedCol, method),
    onSuccess: (data) => {
      toast.success("Encoding applied", {
        description: data.message || `Successfully encoded ${selectedCol}.`,
      });

      // Update session columns
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
      setSelectedCol(""); // Reset selection
    },
    onError: (err: any) => {
      toast.error("Failed to apply encoding", {
        description: err?.response?.data?.message || err.message,
      });
    },
  });

  // Fetch preview when variables change
  useEffect(() => {
    if (sessionId && selectedCol && method) {
      previewMutation.mutate();
    }
  }, [sessionId, selectedCol, method]);

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const sampleBefore = previewMutation.data?.sample_before || [];
  const sampleAfter = previewMutation.data?.sample_after || [];

  const handleApply = () => {
    if (!selectedCol) return;
    applyMutation.mutate();
  };

  const handleUndo = () => {
    undoMutation.mutate();
  };

  return (
    <div>
      <PageHeader
        eyebrow="Transform"
        title="Categorical Encoding"
        description="Translate categorical columns into numeric features ready for any ML model."
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

      {inspectQuery.isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Analyzing columns for categories...</p>
        </div>
      ) : (
        <div className="grid lg:grid-cols-[1fr_1.3fr] gap-6">
          {/* Categorical Columns list */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card rounded-2xl p-6"
          >
            <div className="text-[10px] uppercase tracking-widest text-primary mb-3 flex items-center gap-1.5">
              <Tags className="w-3.5 h-3.5" /> Categorical Columns
            </div>
            {categoricalColumns.length === 0 ? (
              <div className="text-center py-12 text-sm text-muted-foreground border border-dashed rounded-xl">
                No categorical columns found in the dataset.
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-xs uppercase tracking-widest text-muted-foreground bg-secondary/20">
                      <tr>
                        <th className="text-left p-3">Column</th>
                        <th className="text-left p-3">Unique Values</th>
                        <th className="text-left p-3">Suggested</th>
                      </tr>
                    </thead>
                    <tbody>
                      {categoricalColumns.map((c) => {
                        const isSelected = selectedCol === c.name;
                        const suggest = c.unique <= 2 ? "Label" : "One-Hot";
                        return (
                          <tr
                            key={c.name}
                            onClick={() => setSelectedCol(c.name)}
                            className={`border-t border-border/40 cursor-pointer transition ${
                              isSelected ? "bg-primary/10 border-primary" : "hover:bg-secondary/25"
                            }`}
                          >
                            <td className="p-3 font-medium flex items-center gap-1">
                              {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-primary" />}
                              {c.name}
                            </td>
                            <td className="p-3 text-muted-foreground">{c.unique}</td>
                            <td className="p-3">
                              <span className="text-[10px] uppercase tracking-widest border border-primary/30 bg-primary/10 text-primary rounded-full px-2.5 py-0.5">
                                {suggest}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                <div className="mt-6 flex flex-wrap gap-2">
                  {[
                    { label: "Label Encoding", val: "label" },
                    { label: "One-Hot Encoding", val: "onehot" },
                  ].map((s) => (
                    <button
                      key={s.val}
                      onClick={() => setMethod(s.val as any)}
                      className={`px-3 py-2 rounded-lg text-xs font-semibold transition ${
                        method === s.val
                          ? "bg-gradient-brand text-white shadow-[var(--glow-orange)]"
                          : "border border-border hover:border-primary"
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                  {selectedCol && (
                    <button
                      onClick={handleApply}
                      disabled={applyMutation.isPending}
                      className="ml-auto inline-flex items-center gap-1 bg-gradient-brand text-white font-semibold text-xs px-4 py-2 rounded-lg shadow-[var(--glow-orange)] hover:opacity-90 transition disabled:opacity-50"
                    >
                      {applyMutation.isPending && <Loader2 className="w-3 h-3 animate-spin" />}
                      Apply to {selectedCol}
                    </button>
                  )}
                </div>
              </>
            )}
          </motion.div>

          {/* Preview Panel */}
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-card rounded-2xl p-6"
          >
            <div className="text-[10px] uppercase tracking-widest text-primary mb-3">
              Preview: {selectedCol || "Select column"} → {method === "label" ? "Label" : "One-Hot"}
            </div>

            {previewMutation.isPending ? (
              <div className="flex justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : sampleBefore.length === 0 ? (
              <div className="text-center py-12 text-sm text-muted-foreground border border-dashed rounded-xl">
                Select a column from the list to preview the categorical encoding.
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
                    Before (Original)
                  </div>
                  <table className="w-full text-xs">
                    <thead className="text-muted-foreground bg-secondary/10">
                      <tr>
                        <th className="text-left py-1.5 px-2 font-mono">{selectedCol}</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono">
                      {sampleBefore.map((row, i) => (
                        <tr key={i} className="border-t border-border/40 hover:bg-secondary/15">
                          <td className="py-1.5 px-2">{String(row[selectedCol])}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div>
                  <div className="text-[10px] uppercase tracking-widest text-primary mb-2">
                    After (Encoded)
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead className="text-muted-foreground bg-secondary/10">
                        <tr>
                          {sampleAfter.length > 0 &&
                            Object.keys(sampleAfter[0]).map((h) => (
                              <th key={h} className="text-left py-1.5 px-2 font-mono whitespace-nowrap">
                                {h}
                              </th>
                            ))}
                        </tr>
                      </thead>
                      <tbody className="font-mono">
                        {sampleAfter.map((row, i) => (
                          <tr key={i} className="border-t border-border/40 hover:bg-secondary/15">
                            {Object.keys(row).map((k) => (
                              <td
                                key={k}
                                className={`py-1.5 px-2 ${row[k] ? "text-primary font-bold" : "text-muted-foreground"}`}
                              >
                                {String(row[k])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      )}
    </div>
  );
}