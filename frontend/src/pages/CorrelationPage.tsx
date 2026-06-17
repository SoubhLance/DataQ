import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useEffect, useState, useMemo } from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { useSession } from "@/context/SessionContext";
import { inspectService } from "@/services/inspectService";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Sliders } from "lucide-react";



function cellColor(v: number | null) {
  if (v === null) return "rgba(255,255,255,0.05)";
  const a = Math.abs(v);
  if (v >= 0) return `oklch(0.72 0.21 45 / ${a})`; // Warm colors for positive corr
  return `oklch(0.6 0.24 25 / ${a})`; // Cool colors for negative corr
}

export default function CorrelationPage() {
  useEffect(() => {
    document.title = "Correlation — DataQ";
  }, []);
  const { sessionId } = useSession();
  const navigate = useNavigate();
  const [threshold, setThreshold] = useState(0.85);

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  const correlationQuery = useQuery({
    queryKey: ["dataset", "correlation", sessionId, threshold],
    queryFn: () => inspectService.getCorrelationMatrix(threshold),
    enabled: !!sessionId,
  });

  const inspectQuery = useQuery({
    queryKey: ["dataset", "inspect", sessionId],
    queryFn: () => inspectService.getInspection(),
    enabled: !!sessionId,
  });

  const corrData = correlationQuery.data;
  const features = useMemo(() => {
    if (!corrData?.matrix) return [];
    return Object.keys(corrData.matrix);
  }, [corrData]);

  // Target suggestion for relative importance
  const targetCol = useMemo(() => {
    if (!inspectQuery.data?.columns) return "";
    const list = inspectQuery.data.columns;
    return list[list.length - 1]?.name || "";
  }, [inspectQuery.data]);

  // Compute correlation with target
  const targetImportance = useMemo(() => {
    if (!corrData?.matrix || !targetCol) return [];
    return Object.keys(corrData.matrix)
      .map((name) => {
        const val = corrData.matrix[name]?.[targetCol];
        return {
          name,
          v: val !== undefined && val !== null ? Math.abs(val) : 0,
        };
      })
      .filter((item) => item.name !== targetCol)
      .sort((a, b) => b.v - a.v);
  }, [corrData, targetCol]);

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const isLoading = correlationQuery.isLoading || inspectQuery.isLoading;

  return (
    <div>
      <PageHeader
        eyebrow="Relationships"
        title="Correlation & Importance"
        description="Spot multicollinearity, select top features, and identify drivers of your target."
      />

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Computing Pearson correlation matrix...</p>
        </div>
      ) : (
        <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6">
          {/* Correlation matrix */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card rounded-2xl p-6 overflow-hidden"
          >
            <div className="flex justify-between items-center mb-6">
              <div className="text-[10px] uppercase tracking-widest text-primary font-bold">
                Pearson Correlation Matrix
              </div>
              <div className="flex items-center gap-2 text-xs">
                <Sliders className="w-3.5 h-3.5 text-muted-foreground" />
                <span>Threshold:</span>
                <input
                  type="range"
                  min="0.5"
                  max="0.99"
                  step="0.05"
                  value={threshold}
                  onChange={(e) => setThreshold(Number(e.target.value))}
                  className="w-24 accent-primary"
                />
                <span className="font-mono">{threshold}</span>
              </div>
            </div>

            {features.length === 0 ? (
              <div className="text-center py-12 text-sm text-muted-foreground border border-dashed rounded-xl">
                No numeric columns found to calculate correlation matrix.
              </div>
            ) : (
              <div className="overflow-auto max-h-[500px]">
                <table className="text-xs border-separate border-spacing-1">
                  <thead>
                    <tr>
                      <th></th>
                      {features.map((f) => (
                        <th
                          key={f}
                          className="text-muted-foreground font-normal rotate-[-30deg] origin-left h-16 px-1 whitespace-nowrap"
                        >
                          {f}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {features.map((fRow) => (
                      <tr key={fRow}>
                        <td className="text-muted-foreground pr-3 py-1.5 text-right font-medium whitespace-nowrap">
                          {fRow}
                        </td>
                        {features.map((fCol) => {
                          const val = corrData?.matrix[fRow]?.[fCol] ?? null;
                          return (
                            <td
                              key={fCol}
                              className="text-center rounded font-mono w-12 h-9 text-[10px]"
                              style={{
                                background: cellColor(val),
                                color: val !== null && Math.abs(val) > 0.4 ? "#fff" : "rgba(255,255,255,0.7)",
                              }}
                              title={`${fRow} vs ${fCol}: ${val !== null ? val.toFixed(4) : "N/A"}`}
                            >
                              {val !== null ? val.toFixed(2) : "N/A"}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </motion.div>

          {/* Side panel */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card rounded-2xl p-6"
            >
              <div className="text-[10px] uppercase tracking-widest text-primary mb-3 font-bold">
                Highly Correlated Pairs
              </div>
              {corrData?.highly_correlated.length === 0 ? (
                <div className="text-center py-6 text-xs text-muted-foreground border border-dashed rounded-xl">
                  No pairs exceed |r| &gt; {threshold}.
                </div>
              ) : (
                <ul className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {corrData?.highly_correlated.map((p, idx) => (
                    <li
                      key={idx}
                      className="flex items-center justify-between rounded-lg border border-border/60 px-3 py-2 text-xs"
                    >
                      <span className="truncate max-w-[180px]">
                        {p.column1} ↔ {p.column2}
                      </span>
                      <span className={p.correlation > 0 ? "text-primary font-bold" : "text-destructive font-bold"}>
                        {p.correlation.toFixed(2)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-3 text-[10px] text-muted-foreground">
                Suggestion: drop one of any pair with |r| &gt; {threshold} to avoid multicollinearity.
              </div>
            </motion.div>

            {targetCol && (
              <motion.div
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="glass-card rounded-2xl p-6"
              >
                <div className="text-[10px] uppercase tracking-widest text-primary mb-3 font-bold">
                  Correlation with Target ({targetCol})
                </div>
                {targetImportance.length === 0 ? (
                  <div className="text-center py-6 text-xs text-muted-foreground border border-dashed rounded-xl">
                    No target correlations found.
                  </div>
                ) : (
                  <ul className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                    {targetImportance.map((f) => (
                      <li key={f.name}>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="truncate max-w-[180px]">{f.name}</span>
                          <span className="text-muted-foreground">{(f.v * 100).toFixed(0)}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${f.v * 100}%` }}
                            transition={{ duration: 0.8 }}
                            className="h-full bg-gradient-brand"
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </motion.div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}