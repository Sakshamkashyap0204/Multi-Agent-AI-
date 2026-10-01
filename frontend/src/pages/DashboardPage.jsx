import React, { useState, useEffect } from 'react';
import {
  Layers,
  Cpu,
  FileCheck2,
  CheckCircle2,
  AlertOctagon,
  ArrowRight,
  Play,
  Clock,
  Sparkles,
  Activity,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../services/api';
import { StatusBadge, PriorityBadge } from '../components/common/Badge';

export function DashboardPage() {
  const { stats, refreshStats, navigateTo, liveEvents, setIsNewTaskModalOpen } = useApp();
  const [tasks, setTasks] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tasksData, agentsData] = await Promise.all([
        api.getTasks({ limit: 10 }),
        api.getAgents(),
      ]);
      setTasks(tasksData || []);
      setAgents(agentsData || []);
    } catch (e) {
      console.error('Dashboard load error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Welcome / Demo Action Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Operations Dashboard</h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time multi-agent orchestration, human-in-the-loop approvals, and governance enforcement.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => {
              refreshStats();
              loadData();
            }}
            className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsNewTaskModalOpen(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            <span>Launch New Task</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3.5">
        {/* Active Tasks */}
        <div
          onClick={() => navigateTo('tasks')}
          className="p-4 bg-white rounded-xl border border-slate-200/90 shadow-2xs hover:border-slate-300 cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Active Tasks</span>
            <Layers className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.active_tasks || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">
            {stats.running_tasks || 0} executing right now
          </p>
        </div>

        {/* Running Agents */}
        <div
          onClick={() => navigateTo('agents')}
          className="p-4 bg-white rounded-xl border border-slate-200/90 shadow-2xs hover:border-slate-300 cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Agent Fleet</span>
            <Cpu className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.active_agents || 8}</p>
          <p className="text-[11px] text-emerald-600 mt-1 font-medium">100% Operational</p>
        </div>

        {/* Pending Approvals */}
        <div
          onClick={() => navigateTo('approvals')}
          className={`p-4 rounded-xl border shadow-2xs cursor-pointer transition-all ${
            stats.pending_approvals > 0
              ? 'bg-amber-50/60 border-amber-300 hover:bg-amber-50'
              : 'bg-white border-slate-200/90 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span
              className={`text-xs font-medium uppercase tracking-wider ${
                stats.pending_approvals > 0 ? 'text-amber-800 font-semibold' : 'text-slate-500'
              }`}
            >
              Approvals
            </span>
            <FileCheck2
              className={`w-4 h-4 ${
                stats.pending_approvals > 0 ? 'text-amber-600 animate-bounce' : 'text-amber-500'
              }`}
            />
          </div>
          <p
            className={`text-2xl font-bold ${
              stats.pending_approvals > 0 ? 'text-amber-900' : 'text-slate-900'
            }`}
          >
            {stats.pending_approvals || 0}
          </p>
          <p
            className={`text-[11px] mt-1 font-medium ${
              stats.pending_approvals > 0 ? 'text-amber-700' : 'text-slate-400'
            }`}
          >
            {stats.pending_approvals > 0 ? 'Action required' : 'Zero pending gates'}
          </p>
        </div>

        {/* Completed Tasks */}
        <div
          onClick={() => navigateTo('tasks')}
          className="p-4 bg-white rounded-xl border border-slate-200/90 shadow-2xs hover:border-slate-300 cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Completed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.completed_tasks || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Successfully synthesized</p>
        </div>

        {/* Failed Runs */}
        <div
          onClick={() => navigateTo('tasks')}
          className="p-4 bg-white rounded-xl border border-slate-200/90 shadow-2xs hover:border-slate-300 cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Failed / Alert</span>
            <AlertOctagon className="w-4 h-4 text-rose-500" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{stats.failed_tasks || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Automatic rollbacks</p>
        </div>
      </div>

      {/* Main Section: Active Task Runs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Task Runs & Active Workflows</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Live status, participating specialized agents, and current stage
            </p>
          </div>
          <button
            onClick={() => navigateTo('tasks')}
            className="flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700"
          >
            <span>View All Tasks</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
              <tr>
                <th className="px-5 py-3">Task Name</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Current Agent / Step</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Owner</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-slate-400">
                    Loading task runs...
                  </td>
                </tr>
              ) : tasks.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-slate-400">
                    No tasks found. Click "Launch New Task" to begin.
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr
                    key={task.id}
                    className="hover:bg-slate-50/80 transition-colors cursor-pointer group"
                    onClick={() => navigateTo('run-details', task.id)}
                  >
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-900 group-hover:text-brand-600 transition-colors">
                        {task.name}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate max-w-xs">
                        {task.goal || task.description}
                      </div>
                    </td>

                    <td className="px-4 py-3.5">
                      <StatusBadge status={task.status} />
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-1.5 font-medium text-slate-700">
                        {task.current_agent && (
                          <span className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-mono text-[10px]">
                            {task.current_agent}
                          </span>
                        )}
                        <span className="text-slate-600 truncate max-w-[140px]">
                          {task.current_step || '—'}
                        </span>
                      </div>
                    </td>

                    <td className="px-4 py-3.5">
                      <PriorityBadge priority={task.priority} />
                    </td>

                    <td className="px-4 py-3.5 text-slate-600">
                      {task.owner_name || 'System Operator'}
                    </td>

                    <td className="px-4 py-3.5 text-slate-500 font-mono text-[11px]">
                      {task.created_at
                        ? new Date(task.created_at).toLocaleDateString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : '—'}
                    </td>

                    <td className="px-4 py-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigateTo('run-details', task.id);
                        }}
                        className="px-2.5 py-1 text-[11px] font-medium rounded border border-slate-200 bg-white hover:bg-slate-100 text-slate-700 transition-colors shadow-2xs"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Two Column Layout: Recent Activity Feed & Agent Health Fleet */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Real-Time Activity Feed */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-xs p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-brand-600" />
              <h2 className="text-sm font-bold text-slate-900">Live Orchestration Activity</h2>
            </div>
            <span className="text-[11px] font-mono text-slate-400">Real-time Stream</span>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
            {liveEvents.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                Listening for real-time multi-agent orchestration events...
              </div>
            ) : (
              liveEvents.map((evt) => (
                <div
                  key={evt.id}
                  className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 bg-slate-50/60 hover:bg-slate-50 transition-colors"
                >
                  <div className="mt-0.5">
                    {evt.type === 'agent_started' ? (
                      <span className="w-2 h-2 rounded-full bg-blue-500 block mt-1" />
                    ) : evt.type === 'agent_completed' ? (
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
                    ) : evt.type === 'approval_required' ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                    ) : evt.type === 'approval_granted' ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-purple-500" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-slate-400 block mt-1" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-800 leading-snug">{evt.description}</p>
                    <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-1">
                      <span>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                      {evt.agent && <span className="font-mono">agent:{evt.agent}</span>}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right 1 Col: Agent Health & Workload */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-600" />
              <h2 className="text-sm font-bold text-slate-900">Agent Fleet Health</h2>
            </div>
            <button
              onClick={() => navigateTo('agents')}
              className="text-[11px] font-semibold text-brand-600 hover:text-brand-700"
            >
              Manage
            </button>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto pr-1 divide-y divide-slate-100">
            {agents.slice(0, 6).map((agent) => (
              <div key={agent.id} className="pt-2.5 first:pt-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800">{agent.name}</span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Active
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1 font-mono">
                  <span>Success: {agent.success_rate || 100}%</span>
                  <span>Avg: {agent.avg_execution_time || 1.8}s</span>
                  <span>Tasks: {agent.tasks_completed || 0}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
