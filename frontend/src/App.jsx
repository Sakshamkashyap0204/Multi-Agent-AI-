import React, { useState } from 'react';
import { useApp } from './context/AppContext';
import { Sidebar } from './components/layout/Sidebar';
import { TopNavbar } from './components/layout/TopNavbar';
import { GlobalSearchModal } from './components/common/GlobalSearchModal';
import { NewTaskModal } from './components/tasks/NewTaskModal';

// Pages
import { DashboardPage } from './pages/DashboardPage';
import { TasksPage } from './pages/TasksPage';
import { RunDetailsPage } from './pages/RunDetailsPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { AgentsPage } from './pages/AgentsPage';
import { GovernancePage } from './pages/GovernancePage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  const {
    activePage,
    isNewTaskModalOpen,
    setIsNewTaskModalOpen,
    isSearchModalOpen,
    setIsSearchModalOpen,
  } = useApp();

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  const renderActivePage = () => {
    switch (activePage) {
      case 'dashboard':
        return <DashboardPage />;
      case 'tasks':
        return <TasksPage />;
      case 'runs':
      case 'run-details':
        return <RunDetailsPage />;
      case 'approvals':
        return <ApprovalsPage />;
      case 'agents':
        return <AgentsPage />;
      case 'governance':
        return <GovernancePage />;
      case 'audit':
        return <AuditLogsPage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 flex">
      {/* Sidebar Navigation */}
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
        isMobileOpen={isMobileSidebarOpen}
        setIsMobileOpen={setIsMobileSidebarOpen}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-200 ${
          isSidebarCollapsed ? 'md:pl-18' : 'md:pl-64'
        }`}
      >
        {/* Top Navbar */}
        <TopNavbar
          isCollapsed={isSidebarCollapsed}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
        />

        {/* Page Content Container */}
        <main className="flex-1 pt-20 px-4 sm:px-6 lg:px-8 pb-12 max-w-7xl w-full mx-auto">
          {renderActivePage()}
        </main>
      </div>

      {/* Global Modals */}
      <NewTaskModal
        isOpen={isNewTaskModalOpen}
        onClose={() => setIsNewTaskModalOpen(false)}
      />

      <GlobalSearchModal
        isOpen={isSearchModalOpen}
        onClose={() => setIsSearchModalOpen(false)}
      />
    </div>
  );
}

export default App;
