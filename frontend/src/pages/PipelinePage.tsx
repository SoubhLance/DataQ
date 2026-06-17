import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Upload, Copy, AlertTriangle, Sliders, Tags, Download, Check, ArrowDown, FileCode, Loader2, Play } from "lucide-react";
import { useState, useEffect, useMemo } from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { useSession } from "@/context/SessionContext";
import { pipelineService } from "@/services/pipelineService";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";



const getIcon = (type: string) => {
  const t = type.toLowerCase();
  if (t.includes("upload")) return Upload;
  if (t.includes("dup")) return Copy;
  if (t.includes("miss") || t.includes("imput")) return AlertTriangle;
  if (t.includes("outlier") || t.includes("anomaly")) return Sliders;
  if (t.includes("scale") || t.includes("norm")) return Sliders;
  if (t.includes("encod") || t.includes("col")) return Tags;
  return FileCode;
};

const formats = [
  { id: "pandas", label: "Pandas Script", filename: "preprocess.py" },
  { id: "sklearn", label: "Sklearn Pipeline", filename: "pipeline.py" },
  { id: "notebook", label: "Jupyter Notebook", filename: "pipeline.ipynb" },
  { id: "yaml", label: "YAML Recipe", filename: "recipe.yaml" },
] as const;

export default function PipelinePage() {
  useEffect(() => {
    document.title = "Pipeline — DataQ";
  }, []);
  const { sessionId, filename } = useSession();
  const navigate = useNavigate();
  const [format, setFormat] = useState<"pandas" | "sklearn" | "notebook" | "yaml">("pandas");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  const operationsQuery = useQuery({
    queryKey: ["dataset", "operations", sessionId],
    queryFn: () => pipelineService.getOperationsHistory(),
    enabled: !!sessionId,
  });

  const pipelineQuery = useQuery({
    queryKey: ["dataset", "pipeline", sessionId, format],
    queryFn: () => pipelineService.getPipelineCode(format),
    enabled: !!sessionId && !!format,
  });

  const ops = operationsQuery.data || [];
  const pipelineCode = pipelineQuery.data?.pipeline || "";

  // Combine initial upload and applied operations for visualization
  const visualSteps = useMemo(() => {
    const list = [{ label: `Upload: ${filename || "dataset"}`, type: "upload" }];
    ops.forEach((op) => {
      list.push({
        label: op.description,
        type: op.type,
      });
    });
    return list;
  }, [ops, filename]);

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const handleCopy = () => {
    let textToCopy = pipelineCode;
    if (format === "notebook") {
      try {
        textToCopy = JSON.stringify(JSON.parse(pipelineCode), null, 2);
      } catch (e) {}
    }
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleDownload = () => {
    if (!pipelineQuery.data) return;
    const item = formats.find((f) => f.id === format);
    const fname = item ? item.filename : "pipeline.txt";

    let content = pipelineCode;
    if (format === "notebook") {
      try {
        content = JSON.stringify(JSON.parse(pipelineCode), null, 2);
      } catch (e) {}
    }

    const blob = new Blob([content], { type: pipelineQuery.data.content_type });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", fname);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
    toast.success(`Downloaded ${fname}`);
  };

  const isPipelineLoading = pipelineQuery.isLoading;

  return (
    <div>
      <PageHeader
        eyebrow="Workflow"
        title="Pipeline Builder"
        description="A visual record of every transformation — exportable as production-ready Python."
      />

      <div className="grid lg:grid-cols-[280px_1fr] gap-6">
        {/* Left Side: Visual steps flow */}
        <div className="glass-card rounded-2xl p-6 h-fit max-h-[600px] overflow-y-auto">
          <div className="text-[10px] uppercase tracking-widest text-primary mb-4 font-bold">
            Execution Flow
          </div>
          <div className="flex flex-col items-center gap-2">
            {visualSteps.map((s, i) => {
              const Icon = getIcon(s.type);
              return (
                <div key={i} className="flex flex-col items-center w-full">
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.05 }}
                    className={`flex items-center gap-3 rounded-xl border p-3 w-full ${
                      i === visualSteps.length - 1
                        ? "border-primary bg-primary/10 shadow-[0_0_15px_rgba(255,122,0,0.15)] text-primary"
                        : "border-border bg-card/60"
                    }`}
                  >
                    <div className="grid place-items-center w-7 h-7 rounded-lg bg-gradient-brand text-white shrink-0">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-semibold truncate leading-tight" title={s.label}>
                      {s.label}
                    </span>
                  </motion.div>
                  {i < visualSteps.length - 1 && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: 16 }}
                      className="w-px bg-primary/40 my-1 relative"
                    >
                      <ArrowDown className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2.5 h-2.5 text-primary" />
                    </motion.div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side: Code viewer */}
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {formats.map((f) => (
              <button
                key={f.id}
                onClick={() => setFormat(f.id)}
                className={`text-xs px-3.5 py-2 rounded-lg font-semibold transition ${
                  format === f.id
                    ? "bg-gradient-brand text-white shadow-[var(--glow-orange)]"
                    : "border border-border bg-card/20 hover:border-primary"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card rounded-2xl overflow-hidden border border-border/60"
          >
            <div className="flex items-center justify-between px-5 py-3 border-b border-border/60 bg-secondary/40">
              <div className="text-[10px] uppercase tracking-widest text-primary font-bold">
                {formats.find((f) => f.id === format)?.filename}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCopy}
                  className="text-xs px-3 py-1.5 rounded-lg border border-border bg-background hover:border-primary inline-flex items-center gap-1.5 font-medium transition"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-primary animate-scaleIn" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      Copy
                    </>
                  )}
                </button>
                <button
                  onClick={handleDownload}
                  className="text-xs px-3 py-1.5 rounded-lg bg-gradient-brand text-white font-semibold shadow-[var(--glow-orange)] inline-flex items-center gap-1.5 hover:opacity-90 transition"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download
                </button>
              </div>
            </div>

            {isPipelineLoading ? (
              <div className="h-96 flex flex-col items-center justify-center bg-card/20">
                <Loader2 className="w-8 h-8 animate-spin text-primary mb-2" />
                <p className="text-xs text-muted-foreground">Generating script content...</p>
              </div>
            ) : (
              <pre className="p-6 text-xs leading-relaxed font-mono overflow-auto max-h-[500px] bg-card/10 select-text">
                <code className="text-foreground/90 whitespace-pre-wrap block">
                  {format === "notebook" ? (
                    (() => {
                      try {
                        return JSON.stringify(JSON.parse(pipelineCode), null, 2);
                      } catch (e) {
                        return pipelineCode;
                      }
                    })()
                  ) : (
                    pipelineCode
                  )}
                </code>
              </pre>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}