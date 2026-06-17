import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useEffect } from "react";
import { Gauge, AlertCircle, ScatterChart, FileJson, FileSpreadsheet, FileCode, Loader2, Copy } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { useSession } from "@/context/SessionContext";
import { reportService } from "@/services/reportService";
import { pipelineService } from "@/services/pipelineService";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { ReportResponse } from "@/types/report";



export default function ReportsPage() {
  useEffect(() => {
    document.title = "Reports — DataQ";
  }, []);
  const { sessionId, filename } = useSession();
  const navigate = useNavigate();

  useEffect(() => {
    if (!sessionId) {
      navigate("/dashboard/upload");
    }
  }, [sessionId, navigate]);

  const reportQuery = useQuery({
    queryKey: ["dataset", "report", sessionId],
    queryFn: () => reportService.generateJsonReport(false) as Promise<ReportResponse>,
    enabled: !!sessionId,
  });

  if (!sessionId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const reportData = reportQuery.data;
  const isLoading = reportQuery.isLoading;

  const handleDownloadJSON = () => {
    if (!reportData) return;
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${filename ? filename.split(".")[0] : "dataset"}_report.json`);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
    toast.success("Downloaded report JSON");
  };

  const handleDownloadCSV = async () => {
    try {
      toast.info("Preparing dataset download...");
      await reportService.downloadCleanedFile("csv", filename || "dataset.csv");
      toast.success("Downloaded cleaned CSV");
    } catch (e) {
      toast.error("Download failed");
    }
  };

  const handleDownloadPython = async () => {
    try {
      toast.info("Generating preprocessing script...");
      const codeData = await pipelineService.getPipelineCode("pandas");
      const blob = new Blob([codeData.pipeline], { type: "text/plain" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `preprocess.py`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success("Downloaded preprocess.py");
    } catch (e) {
      toast.error("Failed to download script");
    }
  };

  const cards = reportData
    ? [
        {
          title: "Quality Score",
          value: `${reportData.quality_score.score} / 100`,
          note:
            reportData.quality_score.warnings.length === 0
              ? "Optimal condition — no warnings!"
              : `${reportData.quality_score.warnings.length} warnings active.`,
          icon: Gauge,
        },
        {
          title: "Missing Summary",
          value: `${reportData.missing.columns_with_missing} Cols`,
          note:
            reportData.missing.columns_with_missing === 0
              ? "All values populated."
              : `${reportData.missing.details.length} columns have missing values.`,
          icon: AlertCircle,
        },
        {
          title: "Outlier Summary",
          value: `${reportData.outliers.columns_with_outliers} Cols`,
          note:
            reportData.outliers.columns_with_outliers === 0
              ? "Zero outliers detected."
              : `${reportData.outliers.details.reduce((sum, d) => sum + d.outliers_count, 0)} outliers found.`,
          icon: ScatterChart,
        },
        {
          title: "Duplicate Rows",
          value: `${reportData.duplicates.duplicate_rows}`,
          note:
            reportData.duplicates.duplicate_rows === 0
              ? "No duplicates found."
              : `${reportData.duplicates.duplicate_percent.toFixed(2)}% of dataset rows.`,
          icon: Copy,
        },
      ]
    : [];

  return (
    <div>
      <PageHeader
        eyebrow="Export"
        title="Reports"
        description="A consolidated quality report — share, archive, or hand off to engineering."
      />

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
          <p className="text-sm text-muted-foreground">Compiling quality report data...</p>
        </div>
      ) : (
        <>
          <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
            {cards.map((c, i) => {
              const Icon = c.icon;
              return (
                <motion.div
                  key={c.title}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="glass-card rounded-2xl p-5 hover:border-primary/40 transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="text-[10px] uppercase tracking-widest text-primary font-bold">{c.title}</div>
                    <Icon className="w-4 h-4 text-primary" />
                  </div>
                  <div className="mt-3 text-3xl font-black text-gradient-brand">{c.value}</div>
                  <div className="text-xs text-muted-foreground mt-2">{c.note}</div>
                </motion.div>
              );
            })}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card rounded-2xl p-8 flex flex-wrap items-center justify-between gap-6"
          >
            <div>
              <div className="text-[10px] uppercase tracking-widest text-primary font-bold">Export Bundle</div>
              <h3 className="text-xl font-bold mt-1">
                {filename ? filename.split(".")[0] : "dataset"}_bundle
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                Includes profile JSON, cleaned dataset in CSV, and pipeline cleaning code.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={handleDownloadJSON}
                className="inline-flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 hover:bg-primary/10 px-4 py-2.5 text-sm font-semibold transition"
              >
                <FileJson className="w-4 h-4 text-primary" />
                Download JSON Report
              </button>
              <button
                onClick={handleDownloadCSV}
                className="inline-flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 hover:bg-primary/10 px-4 py-2.5 text-sm font-semibold transition"
              >
                <FileSpreadsheet className="w-4 h-4 text-primary" />
                Download Cleaned CSV
              </button>
              <button
                onClick={handleDownloadPython}
                className="inline-flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 hover:bg-primary/10 px-4 py-2.5 text-sm font-semibold transition"
              >
                <FileCode className="w-4 h-4 text-primary" />
                Download Python Script
              </button>
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
}