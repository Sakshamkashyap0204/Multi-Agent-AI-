import React, { useState, useRef, useEffect } from 'react';
import {
  Menu,
  Search,
  Bell,
  Plus,
  CheckCircle2,
  AlertTriangle,
  Info,
  ChevronDown,
  Building2,
  User,
  Shield,
  ExternalLink,
} from 'lucide-react';
import { useApp, SEEDED_USERS } from '../../context/AppContext';

export function TopNavbar({ isCollapsed, onOpenMobileSidebar }) {
  const {
    currentUser,
    switchUser,
    currentWorkspace,
    setCurrentWorkspace,
    notifications,
    markNotificationRead,
    navigateTo,
    setIsNewTaskModalOpen,
    setIsSearchModalOpen,
  } = useApp();

  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const notifRef = useRef(null);
  const userMenuRef = useRef(null);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  // Close popovers on click outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setIsNotifOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setIsUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Keyboard shortcut Ctrl+K
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchModalOpen(true);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setIsSearchModalOpen]);

  return (
    <header
      className={`fixed top-0 right-0 z-30 h-16 bg-white border-b border-slate-200 transition-all duration-200 flex items-center justify-between px-4 sm:px-6 ${
        isCollapsed ? 'left-0 md:left-18' : 'left-0 md:left-64'
      }`}
    >
      {/* Left: Mobile hamburger + Workspace selector */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobileSidebar}
          className="p-2 -ml-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 md:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50/80 text-xs font-medium text-slate-700">
          <Building2 className="w-3.5 h-3.5 text-slate-400" />
          <span>{currentWorkspace}</span>
          <span className="text-[10px] text-slate-400 font-mono">v1.4</span>
        </div>
      </div>

      {/* Middle: Global Search trigger */}
      <div className="flex-1 max-w-md mx-4">
        <button
          onClick={() => setIsSearchModalOpen(true)}
          className="w-full flex items-center justify-between px-3.5 py-1.5 rounded-lg bg-slate-100/80 border border-slate-200 text-xs text-slate-400 hover:bg-slate-100 hover:border-slate-300 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <span className="hidden sm:inline">Search tasks, agents, audit trail...</span>
            <span className="sm:hidden">Search...</span>
          </div>
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-white rounded border border-slate-200">
            Ctrl K
          </kbd>
        </button>
      </div>

      {/* Right: Actions, Notifications, Role Switcher, New Task */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Create Task Button */}
        <button
          onClick={() => setIsNewTaskModalOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs hover:shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">New Task</span>
        </button>

        {/* Notifications Dropdown */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setIsNotifOpen(!isNotifOpen)}
            className="relative p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white" />
            )}
          </button>

          {isNotifOpen && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50">
                <span className="text-xs font-semibold text-slate-900">Notifications</span>
                <span className="text-[11px] text-slate-400">{unreadCount} unread</span>
              </div>

              <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-xs text-slate-400">
                    No notifications yet.
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => {
                        markNotificationRead(n.id);
                        if (n.link && n.link.startsWith('/tasks/')) {
                          const taskId = n.link.replace('/tasks/', '');
                          navigateTo('run-details', taskId);
                          setIsNotifOpen(false);
                        } else if (n.link && n.link.startsWith('/approvals')) {
                          navigateTo('approvals');
                          setIsNotifOpen(false);
                        }
                      }}
                      className={`p-3 text-left hover:bg-slate-50 cursor-pointer transition-colors ${
                        !n.is_read ? 'bg-blue-50/40' : ''
                      }`}
                    >
                      <div className="flex items-start gap-2.5">
                        {n.type === 'warning' ? (
                          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                        ) : n.type === 'success' ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                        ) : (
                          <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-slate-800">{n.title}</p>
                          <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-2">{n.message}</p>
                          <span className="text-[10px] text-slate-400 mt-1 block">
                            {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Role & Profile Switcher */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-100 transition-colors border border-transparent hover:border-slate-200"
          >
            <div className="w-7 h-7 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center font-bold text-xs">
              {currentUser?.full_name?.charAt(0) || 'U'}
            </div>
            <div className="hidden sm:block text-left text-xs">
              <span className="font-semibold text-slate-800 block leading-tight">
                {currentUser?.full_name || 'Loading...'}
              </span>
              <span className="text-[10px] uppercase font-bold tracking-wider text-brand-600 block">
                {currentUser?.role || 'User'}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {isUserMenuOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-100">
              <div className="p-3 border-b border-slate-100 bg-slate-50/50">
                <p className="text-xs font-semibold text-slate-800">{currentUser?.full_name}</p>
                <p className="text-[11px] text-slate-500 truncate">{currentUser?.email}</p>
                <div className="mt-1.5 inline-flex items-center gap-1 px-2 py-0.5 rounded bg-brand-50 text-brand-700 border border-brand-200 text-[10px] font-bold uppercase">
                  <Shield className="w-3 h-3" />
                  Role: {currentUser?.role}
                </div>
              </div>

              {/* Role Switcher for Testing/Demoing RBAC */}
              <div className="p-2">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider px-2 block mb-1">
                  Switch Active Role (Demo)
                </span>
                {SEEDED_USERS.map((u) => (
                  <button
                    key={u.username}
                    onClick={() => {
                      switchUser(u.username);
                      setIsUserMenuOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs text-left transition-colors ${
                      currentUser?.username === u.username
                        ? 'bg-slate-100 text-slate-900 font-semibold'
                        : 'text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <div>
                      <p className="text-xs font-medium">{u.name}</p>
                      <p className="text-[10px] text-slate-400 capitalize">{u.role} · {u.title}</p>
                    </div>
                    {currentUser?.username === u.username && (
                      <span className="w-1.5 h-1.5 rounded-full bg-brand-600" />
                    )}
                  </button>
                ))}
              </div>

              <div className="p-1 border-t border-slate-100">
                <button
                  onClick={() => {
                    navigateTo('settings');
                    setIsUserMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50 rounded-md"
                >
                  Workspace Settings
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
