import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useSession } from "@/context/SessionContext";
import { useDataset } from "@/hooks/useDataset";
import { useQuality } from "@/hooks/useQuality";
import { useOperations } from "@/hooks/useOperations";
import { useQuery } from "@tanstack/react-query";
import { duplicateService } from "@/services/duplicateService";
import { outlierService } from "@/services/outlierService";
import { motion } from "framer-motion";
import { Rows3, Columns3, AlertCircle, Copy, ScatterChart, Gauge, TrendingUp, Loader2 } from "lucide-react";
import {
  AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, RadialBarChart, RadialBar, PolarAngleAxis,
} from "recharts";
import { PageHeader } from "@/components/dashboard/page-header";
import { AnimatedCounter } from "@/components/dashboard/animated-counter";

export default function DashboardPage() {
  const { sessionId } = useSession();
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Dataset Health — DataQ";
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  // Load queries
  const { inspectQuery } = useDataset(sessionId || "");
  const { qualityQuery } = useQuality(sessionId || "");
  const { operationsQuery } = useOperations(sessionId || "");

  const duplicatesQuery = useQuery({
    queryKey: ["dataset", "duplicates", sessionId],
    queryFn: () => duplicateService.getDuplicates(),
    enabled: !!sessionId,
  });

  const outliersQuery = useQuery({
    queryKey: ["dataset", "outliers", sessionId],
    queryFn: () => outlierService.getOutliers("iqr"),
    enabled: !!sessionId,
  });

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const isLoading =
    inspectQuery.isLoading ||
    qualityQuery.isLoading ||
    operationsQuery.isLoading ||
    duplicatesQuery.isLoading ||
    outliersQuery.isLoading;

  const totalMissing = inspectQuery.data
    ? inspectQuery.data.columns.reduce((acc, col) => acc + col.missing, 0)
    : 0;
  const totalCells = inspectQuery.data
    ? inspectQuery.data.shape[0] * inspectQuery.data.shape[1]
    : 1;
  const missingPercent = totalCells > 0 ? (totalMissing / totalCells) * 100 : 0;

  const stats = [
    {
      label: "Rows",
      value: inspectQuery.data?.shape[0] || 0,
      icon: Rows3,
      color: "from-primary/30 to-primary/0",
    },
    {
      label: "Columns",
      value: inspectQuery.data?.shape[1] || 0,
      icon: Columns3,
      color: "from-accent/30 to-accent/0",
    },
    {
      label: "Missing %",
      value: Number(missingPercent.toFixed(1)),
      suffix: "%",
      icon: AlertCircle,
      color: "from-destructive/30 to-destructive/0",
    },
    {
      label: "Duplicates",
      value: duplicatesQuery.data?.duplicate_rows || 0,
      icon: Copy,
      color: "from-primary/30 to-primary/0",
    },
    {
      label: "Outlier Count",
      value: outliersQuery.data?.columns.reduce((sum, col) => sum + col.outliers, 0) || 0,
      icon: ScatterChart,
      color: "from-accent/30 to-accent/0",
    },
    {
      label: "Quality Score",
      value: qualityQuery.data?.score || 0,
      suffix: "/100",
      icon: Gauge,
      color: "from-primary/30 to-destructive/20",
    },
  ];

  const ops = operationsQuery.data || [];

  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      return date.toLocaleDateString();
    } catch (e) {
      return "Recently";
    }
  };

  // Build simulated progress curve from baseline up to current quality score
  const currentScore = qualityQuery.data?.score || 90;
  const numOps = ops.length;
  const timeline = Array.from({ length: Math.max(10, numOps + 3) }).map((_, i) => {
    const baseline = Math.max(45, currentScore - 15);
    const scoreVal =
      numOps === 0
        ? Math.min(100, baseline + i * 2 + Math.sin(i) * 1.5)
        : i < numOps
          ? Math.min(100, baseline + (i / numOps) * (currentScore - baseline) + Math.random() * 2)
          : currentScore;
    return {
      day: `Step ${i + 1}`,
      score: Math.round(scoreVal),
    };
  });

  return (
    <div>
      <PageHeader
        eyebrow="Overview"
        title="Dataset Health"
        description="A real-time snapshot of dataset quality, drift, and recent preprocessing operations."
      />

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Calculating health metrics...</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            {stats.map((s, i) => {
              const Icon = s.icon;
              return (
                <motion.div
                  key={s.label}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05, duration: 0.5 }}
                  className="glass-card rounded-2xl p-5 relative overflow-hidden group hover:border-primary/40 transition"
                >
                  <div
                    className={`absolute inset-0 bg-gradient-to-br ${s.color} opacity-50 group-hover:opacity-100 transition`}
                  />
                  <div className="relative flex items-center justify-between">
                    <span className="text-[10px] uppercase tracking-widest text-muted-foreground">
                      {s.label}
                    </span>
                    <Icon className="w-4 h-4 text-primary" />
                  </div>
                  <div className="relative mt-3 text-3xl font-black text-gradient-brand">
                    <AnimatedCounter
                      value={s.value}
                      decimals={s.decimals ?? 0}
                      suffix={s.suffix ?? ""}
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>

          <div className="grid lg:grid-cols-3 gap-6 mt-8">
            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass-card rounded-2xl p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-primary">
                    Quality Score
                  </p>
                  <h3 className="font-semibold">{currentScore} / 100</h3>
                </div>
                <Gauge className="w-5 h-5 text-primary" />
              </div>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart
                    innerRadius="70%"
                    outerRadius="100%"
                    data={[{ name: "score", value: currentScore, fill: "url(#qg)" }]}
                    startAngle={210}
                    endAngle={-30}
                  >
                    <defs>
                      <linearGradient id="qg" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="oklch(0.72 0.21 45)" />
                        <stop offset="100%" stopColor="oklch(0.6 0.24 25)" />
                      </linearGradient>
                    </defs>
                    <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                    <RadialBar
                      background={{ fill: "rgba(255,255,255,0.05)" }}
                      dataKey="value"
                      cornerRadius={20}
                    />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="glass-card rounded-2xl p-6 lg:col-span-2"
            >
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-primary">
                    Dataset Health Timeline
                  </p>
                  <h3 className="font-semibold">Transformation Progress</h3>
                </div>
                <TrendingUp className="w-5 h-5 text-primary" />
              </div>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timeline}>
                    <defs>
                      <linearGradient id="ta" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="oklch(0.72 0.21 45)" stopOpacity={0.6} />
                        <stop offset="100%" stopColor="oklch(0.72 0.21 45)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="day" stroke="rgba(255,255,255,0.3)" fontSize={10} />
                    <YAxis stroke="rgba(255,255,255,0.3)" fontSize={10} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(15,15,18,0.95)",
                        border: "1px solid rgba(255,122,0,0.3)",
                        borderRadius: 12,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="score"
                      stroke="oklch(0.72 0.21 45)"
                      strokeWidth={2}
                      fill="url(#ta)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="glass-card rounded-2xl p-6 mt-8"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-primary">
                  Recent Operations
                </p>
                <h3 className="font-semibold">Audit log</h3>
              </div>
            </div>
            <div className="overflow-hidden rounded-xl border border-border/60">
              <table className="w-full text-sm">
                <thead className="bg-secondary/40 text-xs uppercase tracking-widest text-muted-foreground">
                  <tr>
                    <th className="text-left px-4 py-3">When</th>
                    <th className="text-left px-4 py-3">Operation</th>
                    <th className="text-left px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {ops.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="text-center py-6 text-muted-foreground">
                        No preprocessing operations applied yet.
                      </td>
                    </tr>
                  ) : (
                    ops.map((o, i) => (
                      <tr
                        key={i}
                        className="border-t border-border/40 hover:bg-secondary/20 transition"
                      >
                        <td className="px-4 py-3 text-muted-foreground">{formatTime(o.time)}</td>
                        <td className="px-4 py-3">{o.description}</td>
                        <td className="px-4 py-3">
                          <span
                            className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] uppercase tracking-widest bg-primary/15 text-primary"
                          >
                            success
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
}
