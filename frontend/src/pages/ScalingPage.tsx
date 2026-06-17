import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { useSession } from "@/context/SessionContext";
import { useDataset } from "@/hooks/useDataset";
import { scalingService } from "@/services/scalingService";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useOperations } from "@/hooks/useOperations";
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts";
import { Loader2, Sliders, Undo2 } from "lucide-react";
import { toast } from "sonner";



const scalers = [
  { id: "standard", name: "StandardScaler", hint: "μ = 0, σ = 1", best: "Linear / SVM" },
  { id: "minmax", name: "MinMaxScaler", hint: "Range [0, 1]", best: "Neural Nets" },
  { id: "robust", name: "RobustScaler", hint: "Resistant to outliers", best: "Tree-based / Outliers" },
];

export default function ScalingPage() {
  useEffect(() => {
    document.title = "Scaling — DataQ";
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
  const [activeScaler, setActiveScaler] = useState<"standard" | "minmax" | "robust">("standard");

  useEffect(() => {
    if (numericColumns.length > 0 && !selectedCol) {
      setSelectedCol(numericColumns[0]);
    }
  }, [numericColumns, selectedCol]);

  const previewMutation = useMutation({
    mutationFn: () => scalingService.previewScaling([selectedCol], activeScaler),
    onError: (err: any) => {
      toast.error("Scaling preview failed", {
        description: err?.response?.data?.message || err.message,
      });
    },
  });

  const applyMutation = useMutation({
    mutationFn: () => scalingService.applyScaling([selectedCol], activeScaler),
    onSuccess: (data) => {
      toast.success("Scaling applied", {
        description: data.message || `Successfully applied ${activeScaler} to ${selectedCol}.`,
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
    },
    onError: (err: any) => {
      toast.error("Failed to apply scaling", {
        description: err?.response?.data?.message || err.message,
      });
    },
  });

  // Trigger preview when column or method changes
  useEffect(() => {
    if (sessionId && selectedCol && activeScaler) {
      previewMutation.mutate();
    }
  }, [sessionId, selectedCol, activeScaler]);

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const sampleBefore = previewMutation.data?.sample_before || [];
  const sampleAfter = previewMutation.data?.sample_after || [];

  // Map raw data points to line charts
  const beforeChartData = sampleBefore.map((row, idx) => ({
    x: `Row ${idx + 1}`,
    value: row[selectedCol] !== null ? Number(row[selectedCol]) : 0,
  }));

  const afterChartData = sampleAfter.map((row, idx) => ({
    x: `Row ${idx + 1}`,
    value: row[selectedCol] !== null ? Number(row[selectedCol]) : 0,
  }));

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
        eyebrow="Normalize"
        title="Feature Scaling"
        description="Bring features onto a common scale so models train faster and converge better."
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

      {/* Scaler Choice Grid */}
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        {scalers.map((s, i) => (
          <motion.button
            key={s.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            onClick={() => setActiveScaler(s.id as any)}
            className={`text-left glass-card rounded-2xl p-5 transition ${
              activeScaler === s.id
                ? "border-primary/50 shadow-[var(--glow-orange)]"
                : "border-border/60 hover:border-primary/30"
            }`}
          >
            <div className="text-[10px] uppercase tracking-widest text-primary font-bold">{s.name}</div>
            <div className="text-xs text-muted-foreground mt-2">{s.hint}</div>
            <div className="mt-3 text-xs">
              Best for: <span className="text-foreground font-medium">{s.best}</span>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Main Plot Area */}
      {inspectQuery.isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Analyzing numerical scales...</p>
        </div>
      ) : (
        <div className="glass-card rounded-2xl p-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
            <div className="text-[10px] uppercase tracking-widest text-primary flex items-center gap-1.5 font-bold">
              <Sliders className="w-3.5 h-3.5" /> Numerical Features
            </div>
            <div className="flex flex-wrap gap-2">
              {numericColumns.length === 0 ? (
                <span className="text-xs text-muted-foreground">No numerical columns found.</span>
              ) : (
                numericColumns.slice(0, 8).map((f) => (
                  <button
                    key={f}
                    onClick={() => setSelectedCol(f)}
                    className={`text-xs px-3 py-1.5 rounded-lg transition ${
                      selectedCol === f
                        ? "bg-primary/20 border border-primary/40 text-primary font-semibold"
                        : "border border-border hover:border-primary"
                    }`}
                  >
                    {f}
                  </button>
                ))
              )}
            </div>
          </div>

          {previewMutation.isPending ? (
            <div className="flex justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : selectedCol && sampleBefore.length > 0 ? (
            <div className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <Chart title="Original Scale (Before)" data={beforeChartData} color="oklch(0.6 0.24 25)" />
                <Chart title="Transformed Scale (After)" data={afterChartData} color="oklch(0.72 0.21 45)" />
              </div>

              <div className="flex justify-end pt-4 border-t border-border/40">
                <button
                  onClick={handleApply}
                  disabled={applyMutation.isPending}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-brand px-6 py-3 font-semibold text-xs text-white shadow-[var(--glow-orange)] hover:opacity-90 transition disabled:opacity-50"
                >
                  {applyMutation.isPending && <Loader2 className="w-3 h-3 animate-spin" />}
                  Apply {activeScaler} to {selectedCol}
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground border border-dashed rounded-xl">
              Select a numerical column above to preview scaling results.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Chart({ title, data, color }: { title: string; data: { x: string; value: number }[]; color: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-2">{title}</div>
      <div className="h-56 rounded-xl border border-border/60 p-2">
        {data.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
            No preview values.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id={`g-${title}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.7} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="x" stroke="rgba(255,255,255,0.3)" fontSize={9} hide />
              <YAxis stroke="rgba(255,255,255,0.3)" fontSize={9} />
              <Tooltip
                contentStyle={{
                  background: "rgba(15,15,18,0.95)",
                  border: `1px solid ${color}`,
                  borderRadius: 12,
                }}
              />
              <Area type="monotone" dataKey="value" stroke={color} strokeWidth={2} fill={`url(#g-${title})`} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}