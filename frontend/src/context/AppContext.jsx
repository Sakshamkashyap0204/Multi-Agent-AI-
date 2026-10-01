import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import wsClient from '../services/websocket';

const AppContext = createContext(null);

export const SEEDED_USERS = [
  { username: 'admin', role: 'admin', name: 'Alex Chen', title: 'System Administrator' },
  { username: 'manager', role: 'manager', name: 'Sarah Mitchell', title: 'Operations Manager' },
  { username: 'operator', role: 'operator', name: 'James Park', title: 'Operations Specialist' },
];

export function AppProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [currentWorkspace, setCurrentWorkspace] = useState('Global Operations (HQ)');
  const [activePage, setActivePage] = useState('dashboard');
  const [selectedTaskId, setSelectedTaskId] = useState(null);
  const [stats, setStats] = useState({
    total_tasks: 0,
    active_tasks: 0,
    running_tasks: 0,
    completed_tasks: 0,
    failed_tasks: 0,
    waiting_tasks: 0,
    active_agents: 8,
    pending_approvals: 0,
  });
  const [notifications, setNotifications] = useState([]);
  const [liveEvents, setLiveEvents] = useState([]);
  const [isNewTaskModalOpen, setIsNewTaskModalOpen] = useState(false);
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [loadingUser, setLoadingUser] = useState(true);

  // Initialize login as admin by default
  const loginUser = useCallback(async (username) => {
    try {
      const password = `${username}123`;
      const data = await api.login(username, password);
      setCurrentUser(data.user);
      return data.user;
    } catch (err) {
      console.error('Login error:', err);
      // Fallback user object
      const fallback = SEEDED_USERS.find(u => u.username === username) || SEEDED_USERS[0];
      setCurrentUser({
        id: 'user-' + username,
        username: fallback.username,
        full_name: fallback.name,
        role: fallback.role,
        email: `${username}@orchestrate.ai`,
      });
    }
  }, []);

  const switchUser = async (username) => {
    await loginUser(username);
    await refreshStats();
    await refreshNotifications();
  };

  const refreshStats = useCallback(async () => {
    try {
      const data = await api.getTaskStats();
      setStats(data);
    } catch (e) {
      console.warn('Failed to load stats:', e);
    }
  }, []);

  const refreshNotifications = useCallback(async () => {
    try {
      const data = await api.getNotifications();
      setNotifications(data);
    } catch (e) {
      console.warn('Failed to load notifications:', e);
    }
  }, []);

  const markNotificationRead = async (id) => {
    try {
      await api.markNotificationRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    } catch (e) {
      console.warn('Failed to mark read:', e);
    }
  };

  const navigateTo = (page, taskId = null) => {
    setActivePage(page);
    if (taskId) {
      setSelectedTaskId(taskId);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const addLiveEvent = useCallback((event) => {
    setLiveEvents(prev => [
      {
        id: Math.random().toString(36).substring(2, 9),
        timestamp: new Date().toISOString(),
        ...event,
      },
      ...prev.slice(0, 49), // Keep latest 50
    ]);
  }, []);

  // Initial App Setup
  useEffect(() => {
    async function init() {
      setLoadingUser(true);
      await loginUser('admin');
      setLoadingUser(false);
      await refreshStats();
      await refreshNotifications();
    }
    init();
  }, [loginUser, refreshStats, refreshNotifications]);

  // Connect WebSocket & Listeners
  useEffect(() => {
    wsClient.connect('global');

    const offStatus = wsClient.on('connection_status', (data) => {
      setWsConnected(data.connected);
    });

    const offAll = wsClient.on('*', (data) => {
      if (data && data.type) {
        // Map WS event to readable activity
        let description = '';
        if (data.type === 'agent_started') {
          description = `${data.agent_name || data.agent} started: "${data.subtask}"`;
        } else if (data.type === 'agent_completed') {
          description = `${data.agent_name || data.agent} completed: "${data.subtask}" (${data.duration ? data.duration.toFixed(1) + 's' : 'done'})`;
        } else if (data.type === 'plan_created') {
          description = data.message || 'Execution plan generated';
        } else if (data.type === 'governance_event') {
          description = `Policy "${data.policy}" triggered by ${data.agent} (${data.action})`;
        } else if (data.type === 'approval_required') {
          description = `Human approval required for ${data.agent}: "${data.action}"`;
        } else if (data.type === 'approval_granted') {
          description = `Human approval granted. Resuming workflow.`;
        } else if (data.type === 'task_completed') {
          description = `Task completed successfully. Final synthesis produced.`;
        } else if (data.type === 'task_failed') {
          description = `Task failed: ${data.error || 'Unknown error'}`;
        } else {
          description = `Event: ${data.type}`;
        }

        addLiveEvent({
          type: data.type,
          task_id: data.task_id,
          agent: data.agent,
          description,
          raw: data,
        });

        // Trigger stats refresh on major transitions
        if (['task_status_update', 'approval_required', 'approval_granted', 'task_completed', 'task_failed'].includes(data.type)) {
          refreshStats();
          refreshNotifications();
        }
      }
    });

    return () => {
      offStatus();
      offAll();
      wsClient.disconnect();
    };
  }, [addLiveEvent, refreshStats, refreshNotifications]);

  // Periodic polling fallback for stats & notifications
  useEffect(() => {
    const interval = setInterval(() => {
      refreshStats();
      refreshNotifications();
    }, 8000);
    return () => clearInterval(interval);
  }, [refreshStats, refreshNotifications]);

  const value = {
    currentUser,
    switchUser,
    currentWorkspace,
    setCurrentWorkspace,
    activePage,
    setActivePage,
    selectedTaskId,
    setSelectedTaskId,
    navigateTo,
    stats,
    refreshStats,
    notifications,
    refreshNotifications,
    markNotificationRead,
    liveEvents,
    addLiveEvent,
    isNewTaskModalOpen,
    setIsNewTaskModalOpen,
    isSearchModalOpen,
    setIsSearchModalOpen,
    wsConnected,
    loadingUser,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
