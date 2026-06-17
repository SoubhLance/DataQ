import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect, useMemo } from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { useSession } from "@/context/SessionContext";
import { useDataset } from "@/hooks/useDataset";
import { visualizationService } from "@/services/visualizationService";
import { inspectService } from "@/services/inspectService";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend
} from "recharts";
import { Loader2, BarChart3, ScatterChart as ScatterIcon, Layers } from "lucide-react";



const tabs = ["Histogram", "Boxplot Summary", "Scatter Plot", "Class Balance"] as const;

export default function VizPage() {
  const { sessionId } = useSession();
  const navigate = useNavigate();

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  const { inspectQuery } = useDataset(sessionId);

  const numericColumns = inspectQuery.data?.numeric_columns || [];
  const categoricalColumns = inspectQuery.data?.categorical_columns || [];
  const allColumns = inspectQuery.data?.columns.map(c => c.name) || [];

  const [tab, setTab] = useState<typeof tabs[number]>("Histogram");
  const [col1, setCol1] = useState<string>("");
  const [col2, setCol2] = useState<string>("");
  const [catCol, setCatCol] = useState<string>("");

  useEffect(() => {
    if (numericColumns.length > 0 && !col1) {
      setCol1(numericColumns[0]);
    }
    if (numericColumns.length > 1 && !col2) {
      setCol2(numericColumns[1]);
    } else if (numericColumns.length > 0 && !col2) {
      setCol2(numericColumns[0]);
    }
  }, [numericColumns, col1, col2]);

  useEffect(() => {
    if (categoricalColumns.length > 0 && !catCol) {
      setCatCol(categoricalColumns[0]);
    }
  }, [categoricalColumns, catCol]);

  // Queries
  const distQuery = useQuery({
    queryKey: ["dataset", "viz", "dist", sessionId, col1],
    queryFn: () => visualizationService.getColumnDistribution(col1, 15),
    enabled: !!sessionId && tab === "Histogram" && !!col1,
  });

  const boxplotQuery = useQuery({
    queryKey: ["dataset", "viz", "boxplot", sessionId, col1],
    queryFn: () => visualizationService.getColumnBoxplot(col1),
    enabled: !!sessionId && tab === "Boxplot Summary" && !!col1,
  });

  const sampleQuery = useQuery({
    queryKey: ["dataset", "viz", "sample", sessionId],
    queryFn: () => inspectService.getDataframeSample(100),
    enabled: !!sessionId && tab === "Scatter Plot",
  });

  const imbalanceQuery = useQuery({
    queryKey: ["dataset", "viz", "imbalance", sessionId, catCol],
    queryFn: () => inspectService.getClassImbalance(catCol),
    enabled: !!sessionId && tab === "Class Balance" && !!catCol,
  });

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  // Map Histogram bins to Recharts format
  const histogramData = useMemo(() => {
    if (!distQuery.data) return [];
    return distQuery.data.map((bin) => ({
      bin: `${bin.bin_start.toFixed(1)} - ${bin.bin_end.toFixed(1)}`,
      count: bin.count,
    }));
  }, [distQuery.data]);

  // Map Boxplot statistics
  const boxplotStats = boxplotQuery.data;
  const boxplotData = useMemo(() => {
    if (!boxplotStats) return [];
    return [
      { name: "Min", value: boxplotStats.min },
      { name: "Q1", value: boxplotStats.q1 },
      { name: "Median", value: boxplotStats.median },
      { name: "Q3", value: boxplotStats.q3 },
      { name: "Max", value: boxplotStats.max },
    ];
  }, [boxplotStats]);

  // Map Scatter Points
  const scatterData = useMemo(() => {
    if (!sampleQuery.data || !col1 || !col2) return [];
    return sampleQuery.data.map((row) => ({
      x: row[col1] !== null ? Number(row[col1]) : 0,
      y: row[col2] !== null ? Number(row[col2]) : 0,
    }));
  }, [sampleQuery.data, col1, col2]);

  // Map Class Balance Bars
  const balanceData = useMemo(() => {
    if (!imbalanceQuery.data?.class_counts) return [];
    const counts = imbalanceQuery.data.class_counts;
    return Object.keys(counts).map((key) => ({
      name: String(key),
      count: counts[key],
    }));
  }, [imbalanceQuery.data]);

  const isTabLoading =
    (tab === "Histogram" && distQuery.isLoading) ||
    (tab === "Boxplot Summary" && boxplotQuery.isLoading) ||
    (tab === "Scatter Plot" && sampleQuery.isLoading) ||
    (tab === "Class Balance" && imbalanceQuery.isLoading);

  return (
    <div>
      <PageHeader
        eyebrow="Explore"
        title="Visualizations"
        description="Charts powered by Recharts — switch tabs to explore distributions, relationships, and balance."
      />

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`text-xs px-3.5 py-2 rounded-lg transition font-semibold ${
              tab === t
                ? "bg-gradient-brand text-white shadow-[var(--glow-orange)]"
                : "border border-border bg-card/20 hover:border-primary"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Variables Configuration per tab */}
      <div className="glass-card rounded-2xl p-4 mb-6 flex flex-wrap gap-4 items-center">
        {(tab === "Histogram" || tab === "Boxplot Summary") && (
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">
              Select Feature
            </label>
            <select
              value={col1}
              onChange={(e) => setCol1(e.target.value)}
              className="rounded-lg border border-border bg-secondary/60 px-3 py-1.5 text-xs outline-none focus:border-primary"
            >
              {numericColumns.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        )}

        {tab === "Scatter Plot" && (
          <>
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">
                X Axis Variable
              </label>
              <select
                value={col1}
                onChange={(e) => setCol1(e.target.value)}
                className="rounded-lg border border-border bg-secondary/60 px-3 py-1.5 text-xs outline-none focus:border-primary"
              >
                {numericColumns.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">
                Y Axis Variable
              </label>
              <select
                value={col2}
                onChange={(e) => setCol2(e.target.value)}
                className="rounded-lg border border-border bg-secondary/60 px-3 py-1.5 text-xs outline-none focus:border-primary"
              >
                {numericColumns.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}

        {tab === "Class Balance" && (
          <div className="flex flex-col gap-1.5">
            <label className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">
              Select Categorical Column
            </label>
            <select
              value={catCol}
              onChange={(e) => setCatCol(e.target.value)}
              className="rounded-lg border border-border bg-secondary/60 px-3 py-1.5 text-xs outline-none focus:border-primary"
            >
              {categoricalColumns.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Plot Area */}
      <motion.div
        key={tab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card rounded-2xl p-6 h-[480px] flex flex-col justify-between"
      >
        {isTabLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary mb-2" />
            <p className="text-xs text-muted-foreground">Generating plot coordinates...</p>
          </div>
        ) : (
          <div className="flex-1 h-full w-full">
            <ResponsiveContainer width="100%" height="100%">
              {tab === "Histogram" ? (
                histogramData.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
                    Select a column to plot.
                  </div>
                ) : (
                  <BarChart data={histogramData} margin={{ bottom: 30 }}>
                    <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="bin" stroke="rgba(255,255,255,0.3)" fontSize={10} angle={-30} textAnchor="end" />
                    <YAxis stroke="rgba(255,255,255,0.3)" fontSize={10} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(15,15,18,0.95)",
                        border: "1px solid rgba(255,122,0,0.3)",
                        borderRadius: 12,
                      }}
                    />
                    <Bar dataKey="count" fill="oklch(0.72 0.21 45)" radius={[6, 6, 0, 0]} name="Sample count" />
                  </BarChart>
                )
              ) : tab === "Boxplot Summary" ? (
                boxplotData.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
                    Select a column to display boxplot.
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 gap-6 h-full items-center">
                    <div className="h-[320px]">
                      <BarChart data={boxplotData}>
                        <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" fontSize={10} />
                        <YAxis stroke="rgba(255,255,255,0.3)" fontSize={10} />
                        <Tooltip
                          contentStyle={{
                            background: "rgba(15,15,18,0.95)",
                            border: "1px solid rgba(255,122,0,0.3)",
                            borderRadius: 12,
                          }}
                        />
                        <Bar dataKey="value" fill="oklch(0.72 0.21 45)" radius={[6, 6, 0, 0]} />
                      </BarChart>
                    </div>

                    <div className="glass-card rounded-xl p-5 border-border/50 max-h-[340px] overflow-y-auto">
                      <div className="text-xs uppercase tracking-widest text-primary mb-3 font-bold">
                        Five-Number Summary
                      </div>
                      <div className="space-y-2 text-xs">
                        {[
                          { label: "Minimum", val: boxplotStats?.min },
                          { label: "Q1 (25th percentile)", val: boxplotStats?.q1 },
                          { label: "Median (50th percentile)", val: boxplotStats?.median },
                          { label: "Q3 (75th percentile)", val: boxplotStats?.q3 },
                          { label: "Maximum", val: boxplotStats?.max },
                          { label: "Lower Whisker", val: boxplotStats?.lower_whisker },
                          { label: "Upper Whisker", val: boxplotStats?.upper_whisker },
                          { label: "Outliers Found", val: boxplotStats?.outliers.length },
                        ].map((item) => (
                          <div key={item.label} className="flex justify-between py-1.5 border-b border-border/30">
                            <span className="text-muted-foreground">{item.label}</span>
                            <span className="font-mono font-bold text-foreground">
                              {item.val !== undefined && item.val !== null ? item.val : "0"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )
              ) : tab === "Scatter Plot" ? (
                scatterData.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
                    Select columns to plot.
                  </div>
                ) : (
                  <ScatterChart>
                    <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="x" name={col1} stroke="rgba(255,255,255,0.3)" fontSize={10} type="number" />
                    <YAxis dataKey="y" name={col2} stroke="rgba(255,255,255,0.3)" fontSize={10} type="number" />
                    <Tooltip
                      cursor={{ strokeDasharray: "3 3" }}
                      contentStyle={{
                        background: "rgba(15,15,18,0.95)",
                        border: "1px solid rgba(255,122,0,0.3)",
                        borderRadius: 12,
                      }}
                    />
                    <Scatter data={scatterData} fill="oklch(0.72 0.21 45)" fillOpacity={0.7} />
                  </ScatterChart>
                )
              ) : balanceData.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-muted-foreground">
                  Select a categorical variable to view balance.
                </div>
              ) : (
                <BarChart data={balanceData} layout="vertical">
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" />
                  <XAxis type="number" stroke="rgba(255,255,255,0.3)" fontSize={10} />
                  <YAxis dataKey="name" type="category" stroke="rgba(255,255,255,0.3)" fontSize={10} />
                  <Tooltip
                    contentStyle={{
                      background: "rgba(15,15,18,0.95)",
                      border: "1px solid rgba(255,122,0,0.3)",
                      borderRadius: 12,
                    }}
                  />
                  <Bar dataKey="count" fill="oklch(0.6 0.24 25)" radius={[0, 6, 6, 0]} name="Class count" />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        )}
      </motion.div>
    </div>
  );
}