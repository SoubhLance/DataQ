import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { ThemeProvider } from "@/components/theme-provider";
import { SessionProvider } from "@/context/SessionContext";
import { queryClient } from "@/lib/queryClient";
import { BackendStatusBanner } from "@/components/BackendStatusBanner";

// Layout
import DashboardLayout from "@/layouts/DashboardLayout";

// Pages
import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import UploadPage from "@/pages/UploadPage";
import InspectorPage from "@/pages/InspectorPage";
import DuplicatesPage from "@/pages/DuplicatesPage";
import MissingPage from "@/pages/MissingPage";
import OutliersPage from "@/pages/OutliersPage";
import EncodingPage from "@/pages/EncodingPage";
import ScalingPage from "@/pages/ScalingPage";
import CorrelationPage from "@/pages/CorrelationPage";
import VisualizationPage from "@/pages/VisualizationPage";
import AgentPage from "@/pages/AgentPage";
import PipelinePage from "@/pages/PipelinePage";
import ReportsPage from "@/pages/ReportsPage";
import SettingsPage from "@/pages/SettingsPage";

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <ThemeProvider>
          <BrowserRouter>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<LandingPage />} />
              <Route path="/login" element={<LoginPage />} />

              {/* Dashboard Layout & Nested Routes */}
              <Route path="/dashboard" element={<DashboardLayout />}>
                <Route index element={<DashboardPage />} />
                <Route path="upload" element={<UploadPage />} />
                <Route path="inspector" element={<InspectorPage />} />
                <Route path="duplicates" element={<DuplicatesPage />} />
                <Route path="missing" element={<MissingPage />} />
                <Route path="outliers" element={<OutliersPage />} />
                <Route path="encoding" element={<EncodingPage />} />
                <Route path="scaling" element={<ScalingPage />} />
                <Route path="correlation" element={<CorrelationPage />} />
                <Route path="visualizations" element={<VisualizationPage />} />
                <Route path="agent" element={<AgentPage />} />
                <Route path="pipeline" element={<PipelinePage />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
          <BackendStatusBanner />
          <Toaster position="top-right" closeButton richColors />
        </ThemeProvider>
      </SessionProvider>
    </QueryClientProvider>
  );
}
