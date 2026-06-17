import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import { DashboardSidebar } from "@/components/dashboard/sidebar";
import { DashboardTopbar } from "@/components/dashboard/topbar";

export default function DashboardLayout() {
  useEffect(() => {
    document.title = "DataQ — Workspace";
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <DashboardSidebar />
      <div className="lg:pl-64">
        <DashboardTopbar />
        <main className="px-6 md:px-10 py-8 max-w-[1500px] mx-auto">
          <Outlet />
        </main>
      </div>
      <div className="pointer-events-none fixed inset-0 -z-10 grid-bg opacity-30" />
      <div className="pointer-events-none fixed -top-40 -right-32 h-[500px] w-[500px] rounded-full bg-[var(--brand-orange)] opacity-[0.08] blur-[140px] -z-10" />
      <div className="pointer-events-none fixed -bottom-40 -left-32 h-[500px] w-[500px] rounded-full bg-[var(--brand-red)] opacity-[0.06] blur-[140px] -z-10" />
    </div>
  );
}
