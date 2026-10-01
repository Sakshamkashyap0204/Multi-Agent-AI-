import React from 'react';
import {
  LayoutDashboard,
  Layers,
  Cpu,
  PlayCircle,
  ShieldCheck,
  FileCheck2,
  ScrollText,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Wifi,
  WifiOff,
  Sparkles,
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export function Sidebar({ isCollapsed, setIsCollapsed, isMobileOpen, setIsMobileOpen }) {
  const { activePage, navigateTo, stats, wsConnected } = useApp();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'tasks', label: 'Tasks', icon: Layers, badge: stats.total_tasks },
    { id: 'runs', label: 'Runs', icon: PlayCircle, badge: stats.running_tasks > 0 ? stats.running_tasks : null, badgeColor: 'bg-blue-600' },
    { id: 'agents', label: 'Agents', icon: Cpu, badge: stats.active_agents },
    {
      id: 'approvals',
      label: 'Approvals',
      icon: FileCheck2,
      badge: stats.pending_approvals > 0 ? stats.pending_approvals : null,
      badgeColor: 'bg-amber-500 animate-pulse',
    },
    { id: 'governance', label: 'Governance', icon: ShieldCheck },
    { id: 'audit', label: 'Audit Logs', icon: ScrollText },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 md:hidden backdrop-blur-xs"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 bg-white border-r border-slate-200 transition-all duration-200 flex flex-col ${
          isCollapsed ? 'w-18' : 'w-64'
        } ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-200 shrink-0">
          <div
            onClick={() => navigateTo('dashboard')}
            className="flex items-center gap-3 cursor-pointer overflow-hidden select-none"
          >
            <div className="w-9 h-9 rounded-lg bg-brand-600 text-white flex items-center justify-center font-bold text-lg shadow-sm shadow-brand-500/20 shrink-0">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            {!isCollapsed && (
              <div className="min-w-0">
                <span className="font-semibold text-slate-900 text-sm tracking-tight block truncate">
                  Orchestrate<span className="text-brand-600">AI</span>
                </span>
                <span className="text-[10px] text-slate-400 font-medium tracking-tight block truncate uppercase">
                  Multi-Agent Platform
                </span>
              </div>
            )}
          </div>

          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden md:flex p-1.5 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id || (item.id === 'runs' && activePage === 'run-details');

            return (
              <button
                key={item.id}
                onClick={() => {
                  navigateTo(item.id);
                  setIsMobileOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-colors group relative ${
                  isActive
                    ? 'bg-brand-50 text-brand-700 font-semibold shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'
                }`}
                title={isCollapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 transition-colors ${
                    isActive ? 'text-brand-600' : 'text-slate-400 group-hover:text-slate-600'
                  }`}
                />

                {!isCollapsed && <span className="truncate flex-1 text-left">{item.label}</span>}

                {/* Badge count */}
                {item.badge !== null && item.badge !== undefined && (
                  <span
                    className={`ml-auto text-[10px] font-bold px-1.5 py-0.2 rounded-full shrink-0 ${
                      item.badgeColor
                        ? `${item.badgeColor} text-white`
                        : isActive
                        ? 'bg-brand-200 text-brand-800'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Footer Status Panel */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/70 shrink-0">
          <div className="flex items-center gap-2 text-[11px] text-slate-500">
            {wsConnected ? (
              <Wifi className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            ) : (
              <WifiOff className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            )}
            {!isCollapsed && (
              <div className="truncate">
                <span className="font-medium text-slate-700">
                  {wsConnected ? 'Live Connection Active' : 'Connecting to Node...'}
                </span>
                <span className="block text-[10px] text-slate-400">8 Agents Synchronized</span>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
