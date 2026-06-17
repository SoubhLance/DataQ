import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useMemo, useState, useEffect } from "react";
import { Search, Hash, Type, Calendar, ToggleLeft, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { useSession } from "@/context/SessionContext";
import { useDataset } from "@/hooks/useDataset";
import { useQuery } from "@tanstack/react-query";
import { inspectService } from "@/services/inspectService";



const icons = { numeric: Hash, categorical: Type, datetime: Calendar, boolean: ToggleLeft };
const colors = {
  numeric: "bg-primary/15 text-primary border-primary/30",
  categorical: "bg-accent/15 text-accent border-accent/30",
  datetime: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  boolean: "bg-destructive/15 text-destructive border-destructive/30",
};

export default function InspectorPage() {
  const { sessionId } = useSession();
  const navigate = useNavigate();
  const [q, setQ] = useState("");

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const { inspectQuery } = useDataset(sessionId);

  const sampleQuery = useQuery({
    queryKey: ["dataset", "sample", sessionId],
    queryFn: () => inspectService.getDataframeSample(50),
    enabled: !!sessionId,
  });

  const getColType = (dtype: string): "numeric" | "categorical" | "datetime" | "boolean" => {
    const d = dtype.toLowerCase();
    if (d.includes("int") || d.includes("float") || d.includes("double") || d.includes("number")) return "numeric";
    if (d.includes("bool")) return "boolean";
    if (d.includes("date") || d.includes("time")) return "datetime";
    return "categorical";
  };

  const columns = useMemo(() => {
    if (!inspectQuery.data) return [];
    return inspectQuery.data.columns.map((c) => ({
      name: c.name,
      type: getColType(c.dtype),
      unique: c.unique,
      missing: c.missing,
      missing_percent: c.missing_percent,
      dtype: c.dtype,
    }));
  }, [inspectQuery.data]);

  const filtered = useMemo(() => {
    return columns.filter((c) => c.name.toLowerCase().includes(q.toLowerCase()));
  }, [columns, q]);

  const sampleData = sampleQuery.data || [];
  const sampleHeaders = sampleData.length > 0 ? Object.keys(sampleData[0]) : [];

  const isLoading = inspectQuery.isLoading || sampleQuery.isLoading;

  return (
    <div>
      <PageHeader
        eyebrow="Inspect"
        title="Dataset Inspector"
        description="Search, sort, and inspect every column with type detection and stats."
      />

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Inspecting dataset rows and schema...</p>
        </div>
      ) : (
        <div className="grid lg:grid-cols-[1fr_320px] gap-6">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card rounded-2xl p-4 overflow-hidden"
          >
            {sampleData.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No sample data available.
              </div>
            ) : (
              <>
                <div className="overflow-auto rounded-xl border border-border/60 max-h-[600px]">
                  <table className="w-full text-sm">
                    <thead className="bg-secondary/40 text-xs uppercase tracking-widest text-muted-foreground sticky top-0 z-10 backdrop-blur-md">
                      <tr>
                        {sampleHeaders.map((k) => (
                          <th key={k} className="text-left px-4 py-3 whitespace-nowrap bg-card/60">
                            {k}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sampleData.map((row, i) => (
                        <tr
                          key={i}
                          className="border-t border-border/40 hover:bg-secondary/20 transition"
                        >
                          {sampleHeaders.map((h, j) => {
                            const val = row[h];
                            return (
                              <td key={j} className="px-4 py-2.5 font-mono text-xs whitespace-nowrap">
                                {val === null || val === undefined ? (
                                  <span className="text-destructive italic">NaN</span>
                                ) : (
                                  String(val)
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex items-center justify-between mt-4 text-xs text-muted-foreground">
                  <span>
                    Showing {sampleData.length} of {inspectQuery.data?.shape[0].toLocaleString()} rows
                  </span>
                  <span>Total columns: {inspectQuery.data?.shape[1]}</span>
                </div>
              </>
            )}
          </motion.div>

          <motion.aside
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="glass-card rounded-2xl p-5"
          >
            <div className="text-[10px] uppercase tracking-widest text-primary mb-3">Columns</div>
            <div className="relative mb-3">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search columns"
                className="w-full pl-8 pr-3 py-2 rounded-lg bg-secondary/60 border border-border focus:border-primary outline-none text-xs"
              />
            </div>
            <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
              {filtered.length === 0 ? (
                <div className="text-center py-6 text-xs text-muted-foreground">
                  No columns found.
                </div>
              ) : (
                filtered.map((c) => {
                  const Icon = icons[c.type] || Type;
                  return (
                    <div
                      key={c.name}
                      className="rounded-xl border border-border/60 p-3 hover:border-primary/40 transition"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Icon className="w-3.5 h-3.5 text-primary" />
                          <span className="text-sm font-medium truncate max-w-[120px]" title={c.name}>
                            {c.name}
                          </span>
                        </div>
                        <span
                          className={`text-[9px] uppercase tracking-widest border rounded-full px-2 py-0.5 ${
                            colors[c.type] || "bg-secondary text-muted-foreground"
                          }`}
                        >
                          {c.dtype}
                        </span>
                      </div>
                      <div className="mt-2 grid grid-cols-3 gap-2 text-[10px] text-muted-foreground">
                        <div>
                          <div className="text-foreground font-semibold text-xs">{c.unique}</div>
                          unique
                        </div>
                        <div>
                          <div className="text-foreground font-semibold text-xs">{c.missing}</div>
                          missing
                        </div>
                        <div>
                          <div className="text-foreground font-semibold text-xs">
                            {c.missing_percent}%
                          </div>
                          missing %
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </motion.aside>
        </div>
      )}
    </div>
  );
}