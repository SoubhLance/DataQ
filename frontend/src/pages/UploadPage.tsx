import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { UploadCloud, FileSpreadsheet, FileJson, Database, Sparkles, Loader2, ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { uploadService } from "@/services/uploadService";
import { inspectService } from "@/services/inspectService";
import { useSession } from "@/context/SessionContext";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

export default function UploadPage() {
  const navigate = useNavigate();
  const { setSession } = useSession();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [drag, setDrag] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [metadata, setMetadata] = useState<{
    rows: number;
    columns: number;
    memory: string;
    targetSuggestion: string;
    filename: string;
  } | null>(null);

  useEffect(() => {
    document.title = "Upload Dataset — DataQ";
  }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setProgress(0);
    setMetadata(null);

    try {
      const uploadRes = await uploadService.uploadDataset(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
        setProgress(percentCompleted);
      });

      // Save initial session state so subsequent inspect request uses it
      setSession({
        sessionId: uploadRes.session_id,
        filename: uploadRes.filename,
        rows: uploadRes.rows,
        columns: uploadRes.columns,
      });

      // Fetch metadata details
      toast.info("Analyzing dataset structure...", { duration: 2000 });
      const inspectRes = await inspectService.getInspection();

      const allCols = inspectRes.columns.map((c) => c.name);
      const suggestedTarget = allCols[allCols.length - 1] || "None";

      setMetadata({
        rows: inspectRes.shape[0],
        columns: inspectRes.shape[1],
        memory: `${inspectRes.memory_usage_mb.toFixed(2)} MB`,
        targetSuggestion: suggestedTarget,
        filename: uploadRes.filename,
      });

      // Update Session Context with actual inspected counts
      setSession({
        sessionId: uploadRes.session_id,
        filename: uploadRes.filename,
        rows: inspectRes.shape[0],
        columns: inspectRes.shape[1],
      });

      toast.success("Dataset uploaded and analyzed successfully!");
    } catch (error: any) {
      console.error("Upload error:", error);
      const detail = error?.response?.data?.detail;
      const message = error?.response?.data?.message || error?.message;

      if (detail !== "SESSION_NOT_FOUND" && detail !== "SESSION_EXPIRED") {
        // SESSION errors are handled globally by the axios interceptor
        toast.error("Upload Failed", {
          description: message || "Could not reach the backend. Make sure the server is running.",
        });
      }
    } finally {
      setUploading(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUpload(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    if (!uploading) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Step 1"
        title="Upload Dataset"
        description="Drag a file or pick from your system. We support CSV, Excel, JSON, and Parquet."
      />

      <input
        type="file"
        ref={fileInputRef}
        onChange={onFileChange}
        className="hidden"
        accept=".csv,.xlsx,.xls,.json,.parquet"
      />

      <motion.div
        onDragOver={(e) => {
          e.preventDefault();
          if (!uploading) setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          if (uploading) return;
          if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleUpload(e.dataTransfer.files[0]);
          }
        }}
        onClick={triggerFileInput}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`relative cursor-pointer rounded-3xl border-2 border-dashed p-16 text-center transition overflow-hidden ${
          drag
            ? "border-primary bg-primary/10 shadow-[var(--glow-orange)]"
            : "border-border/70 bg-card/40 hover:border-primary/50"
        } ${uploading ? "pointer-events-none opacity-80" : ""}`}
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="absolute inset-0 bg-[conic-gradient(from_0deg,transparent_0%,rgba(255,122,0,0.18)_20%,transparent_40%)] opacity-60 pointer-events-none"
        />
        <div className="relative">
          {uploading ? (
            <div className="flex flex-col items-center justify-center">
              <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
              <h3 className="text-xl font-bold">Uploading {progress}%</h3>
              <div className="w-64 bg-secondary h-2 rounded-full overflow-hidden mt-3">
                <div
                  className="bg-primary h-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          ) : (
            <>
              <div className="mx-auto w-20 h-20 rounded-2xl bg-gradient-brand grid place-items-center shadow-[var(--glow-orange)] mb-6">
                <UploadCloud className="w-10 h-10 text-white" />
              </div>
              <h3 className="text-2xl font-bold">Drop your dataset here</h3>
              <p className="text-sm text-muted-foreground mt-2">or click to browse — up to 2 GB</p>
            </>
          )}

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3 text-xs">
            {[
              { label: "CSV", icon: FileSpreadsheet },
              { label: "Excel", icon: FileSpreadsheet },
              { label: "JSON", icon: FileJson },
              { label: "Parquet", icon: Database },
            ].map((f) => (
              <span
                key={f.label}
                className="inline-flex items-center gap-1.5 rounded-full border border-border bg-secondary/50 px-3 py-1"
              >
                <f.icon className="w-3 h-3 text-primary" /> {f.label}
              </span>
            ))}
          </div>
        </div>
      </motion.div>

      {metadata && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6 mt-8"
        >
          <div className="grid md:grid-cols-4 gap-4">
            {[
              { label: "Rows", value: metadata.rows.toLocaleString() },
              { label: "Columns", value: metadata.columns.toLocaleString() },
              { label: "Memory", value: metadata.memory },
              { label: "Target Suggestion", value: metadata.targetSuggestion, glow: true },
            ].map((c) => (
              <div
                key={c.label}
                className={`glass-card rounded-2xl p-5 ${
                  c.glow ? "border-primary/40 shadow-[var(--glow-orange)]" : ""
                }`}
              >
                <div className="text-[10px] uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
                  {c.glow && <Sparkles className="w-3 h-3 text-primary" />}
                  {c.label}
                </div>
                <div className={`mt-2 text-2xl font-bold ${c.glow ? "text-gradient-brand" : ""}`}>
                  {c.value}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end">
            <Button
              onClick={() => navigate("/dashboard")}
              className="rounded-xl px-6 py-5 bg-gradient-brand text-white font-medium flex items-center gap-2 hover:opacity-95 shadow-[var(--glow-orange)] transition"
            >
              Continue to Dashboard <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        </motion.div>
      )}
    </div>
  );
}
