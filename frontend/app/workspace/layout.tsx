"use client";

import { usePathname } from "next/navigation";
import { useCallback, useState } from "react";
import { Sidebar } from "@/components/sidebar";

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev);
  }, []);

  return (
    <div className={`dashboard-layout ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
      <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />
      <main className="dashboard-main" key={pathname}>
        <div className="dashboard-page" style={{ animation: "fadeSlideIn 0.35s ease both" }}>
          {children}
        </div>
      </main>
    </div>
  );
}
