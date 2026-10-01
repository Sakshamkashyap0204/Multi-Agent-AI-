import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  ArrowLeft,
  Play,
  Pause,
  XCircle,
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Layers,
  Cpu,
  ShieldCheck,
  ChevronRight,
  FileText,
  User,
  ExternalLink,
  RefreshCw,
  Eye,
  Check,
  Sparkles,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../services/api';
import wsClient from '../services/websocket';
import { StatusBadge, PriorityBadge } from '../components/common/Badge';
import { FinalResultView } from '../components/tasks/FinalResultView';
import { RevisionModal } from '../components/tasks/RevisionModal';

export function RunDetailsPage() {
  const { selectedTaskId, navigateTo, currentUser, refreshStats } = useApp();
  const [task, setTask] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [pendingApproval, setPendingApproval] = useState(null);
  const [selectedSubtask, setSelectedSubtask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('timeline'); // timeline | inspector | deliverable | audit
  const [isRevisionOpen, setIsRevisionOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchTaskDetails = useCallback(async () => {
    if (!selectedTaskId) return;
    try {
      const [taskData, execData, auditData, approvalsData] = await Promise.all([
        api.getTask(selectedTaskId),
        api.getTaskExecutions(selectedTaskId).catch(() => []),
        api.getTaskAudit(selectedTaskId).catch(() => []),
        api.getApprovals({ status: 'pending' }).catch(() => []),
      ]);

      setTask(taskData);
      setExecutions(execData || []);
      setAuditLogs(auditData || []);

      // Check if there is an approval waiting for this task
      const matchApproval = (approvalsData || []).find((a) => a.task_id === selectedTaskId);
      setPendingApproval(matchApproval || null);

      // Auto-select active or last completed subtask if not already selected
      if (taskData.subtasks && taskData.subtasks.length > 0 && !selectedSubtask) {
        const running = taskData.subtasks.find((s) => s.status === 'running');
        setSelectedSubtask(running || taskData.subtasks[taskData.subtasks.length - 1]);
      }
    } catch (e) {
      console.error('Error fetching task details:', e);
    } finally {
      setLoading(false);
    }
  }, [selectedTaskId, selectedSubtask]);

  // Initial fetch and WebSocket listener
  useEffect(() => {
    fetchTaskDetails();

    // Listen to WebSocket events for this task
    const offAll = wsClient.on('*', (data) => {
      if (data && (data.task_id === selectedTaskId || data.type?.includes('task'))) {
        fetchTaskDetails();
      }
    });

    // Also poll every 2 seconds while task is in active state
    const interval = setInterval(() => {
      fetchTaskDetails();
    }, 2500);

    return () => {
      offAll();
      clearInterval(interval);
    };
  }, [fetchTaskDetails, selectedTaskId]);

  const handlePause = async () => {
    setActionLoading(true);
    try {
      await api.pauseTask(task.id);
      await fetchTaskDetails();
      refreshStats();
    } finally {
      setActionLoading(false);
    }
  };

  const handleResume = async () => {
    setActionLoading(true);
    try {
      await api.resumeTask(task.id);
      await fetchTaskDetails();
      refreshStats();
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel this task execution?')) return;
    setActionLoading(true);
    try {
      await api.cancelTask(task.id);
      await fetchTaskDetails();
      refreshStats();
    } finally {
      setActionLoading(false);
    }
  };

  const handleApproveAction = async (approvalId) => {
    setActionLoading(true);
    try {
      await api.approve(approvalId, 'Executive authorized progression');
      await fetchTaskDetails();
      refreshStats();
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectAction = async (approvalId) => {
    setActionLoading(true);
    try {
      await api.reject(approvalId, 'Declined by authorized executive');
      await fetchTaskDetails();
      refreshStats();
    } finally {
      setActionLoading(false);
    }
  };

  if (!selectedTaskId) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200">
        <Layers className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-800">No Task Selected</h3>
        <p className="text-xs text-slate-500 mt-1 mb-4">
          Select a task run from the dashboard or tasks list to monitor execution.
        </p>
        <button
          onClick={() => navigateTo('tasks')}
          className="px-4 py-2 bg-brand-600 text-white rounded-lg text-xs font-semibold"
        >
          Browse Tasks
        </button>
      </div>
    );
  }

  if (loading && !task) {
    return (
      <div className="p-12 text-center text-xs text-slate-500">
        Loading execution orchestrator state...
      </div>
    );
  }

  const subtasks = task?.subtasks || [];
  const isCompleted = task?.status === 'COMPLETED';
  const isWaitingApproval = task?.status === 'WAITING_FOR_APPROVAL' || pendingApproval !== null;

  return (
    <div className="space-y-5">
      {/* Top Header & Breadcrumb Bar */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigateTo('tasks')}
              className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-500 transition-colors"
              title="Back to Tasks"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>

            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-lg font-bold text-slate-900 tracking-tight">{task.name}</h1>
                <StatusBadge status={task.status} />
                <PriorityBadge priority={task.priority} />
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                  v{task.version || 1}.0
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1 max-w-2xl">{task.goal || task.description}</p>
            </div>
          </div>

          {/* Action Control Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={fetchTaskDetails}
              className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            {task.status === 'RUNNING' && (
              <button
                onClick={handlePause}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
            )}

            {task.status === 'PAUSED' && (
              <button
                onClick={handleResume}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Resume</span>
              </button>
            )}

            {['RUNNING', 'WAITING_FOR_APPROVAL', 'PLANNING'].includes(task.status) && (
              <button
                onClick={handleCancel}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 rounded-lg transition-colors"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Cancel</span>
              </button>
            )}

            {isCompleted && (
              <button
                onClick={() => setIsRevisionOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-brand-700 bg-brand-50 border border-brand-200 hover:bg-brand-100 rounded-lg transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Request Revision</span>
              </button>
            )}
          </div>
        </div>

        {/* Task Metadata Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 mt-4 border-t border-slate-100 text-xs">
          <div>
            <span className="text-slate-400 block text-[11px]">Owner / Initiator</span>
            <span className="font-medium text-slate-800">{task.owner_name || 'System Operator'}</span>
          </div>

          <div>
            <span className="text-slate-400 block text-[11px]">Governance Mode</span>
            <span className="font-medium text-slate-800 capitalize">
              {task.governance_mode || 'Standard'} Mode
            </span>
          </div>

          <div>
            <span className="text-slate-400 block text-[11px]">Human Oversight</span>
            <span className="font-medium text-slate-800 capitalize">
              {task.human_oversight?.replace(/_/g, ' ') || 'Sensitive Actions'}
            </span>
          </div>

          <div>
            <span className="text-slate-400 block text-[11px]">Current Stage</span>
            <span className="font-medium text-slate-800 truncate block">
              {task.current_step || (isCompleted ? 'Final Synthesis Complete' : 'Initializing')}
            </span>
          </div>
        </div>
      </div>

      {/* Human Approval Required Alert Banner */}
      {isWaitingApproval && pendingApproval && (
        <div className="p-5 rounded-xl bg-amber-50/90 border-2 border-amber-300 shadow-sm animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3.5">
              <div className="p-2 rounded-lg bg-amber-200 text-amber-900 shrink-0 mt-0.5">
                <AlertTriangle className="w-5 h-5 text-amber-800" />
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-amber-950">
                    Human Authorization Required
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-200">
                    Risk: {pendingApproval.risk_level || 'High'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-amber-200/70 text-amber-900">
                    Policy: {pendingApproval.policy_triggered || 'Governance Gate'}
                  </span>
                </div>

                <p className="text-xs text-amber-900 mt-1 font-medium leading-relaxed">
                  {pendingApproval.reason}
                </p>

                <p className="text-[11px] text-amber-800/80 mt-1 font-mono">
                  Triggered by <span className="font-bold">{pendingApproval.agent_slug}</span> agent for action: "{pendingApproval.requested_action}"
                </p>
              </div>
            </div>

            {/* Approval Decision Buttons */}
            <div className="flex items-center gap-2.5 shrink-0 self-end md:self-center">
              <button
                onClick={() => handleRejectAction(pendingApproval.id)}
                disabled={actionLoading}
                className="px-3.5 py-2 text-xs font-semibold text-rose-700 bg-white border border-rose-300 hover:bg-rose-50 rounded-lg shadow-2xs transition-colors"
              >
                Reject Action
              </button>

              <button
                onClick={() => handleApproveAction(pendingApproval.id)}
                disabled={actionLoading}
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-xs transition-colors"
              >
                <Check className="w-4 h-4" />
                <span>Approve & Continue Run</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs Bar */}
      <div className="flex border-b border-slate-200 bg-white px-5 rounded-t-xl">
        <button
          onClick={() => setActiveTab('timeline')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'timeline'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Execution Timeline & Graph</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px] text-slate-600">
            {subtasks.length}
          </span>
        </button>

        {isCompleted && (
          <button
            onClick={() => setActiveTab('deliverable')}
            className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'deliverable'
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Sparkles className="w-4 h-4 text-emerald-600" />
            <span>Final Deliverable Report</span>
          </button>
        )}

        <button
          onClick={() => setActiveTab('inspector')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'inspector'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Cpu className="w-4 h-4" />
          <span>Agent Step Inspector</span>
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'audit'
              ? 'border-brand-600 text-brand-700'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Run Audit Trail</span>
          <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px] text-slate-600">
            {auditLogs.length}
          </span>
        </button>
      </div>

      {/* Main Tab Content */}
      {activeTab === 'timeline' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Sequential & Parallel Steps Timeline (7 cols) */}
          <div className="lg:col-span-7 space-y-3">
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 flex items-center justify-between">
                <span>Multi-Agent Workflow Stages</span>
                <span className="text-[11px] font-normal text-slate-400">
                  Click step to inspect agent payload
                </span>
              </h3>

              <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
                {subtasks.map((st, idx) => {
                  const isSelected = selectedSubtask?.id === st.id;
                  const isStRunning = st.status === 'running';
                  const isStCompleted = st.status === 'completed';
                  const isStFailed = st.status === 'failed';

                  return (
                    <div
                      key={st.id}
                      onClick={() => setSelectedSubtask(st)}
                      className={`relative p-3.5 rounded-lg border transition-all cursor-pointer group ${
                        isSelected
                          ? 'border-brand-500 bg-brand-50/40 ring-1 ring-brand-500/20'
                          : 'border-slate-200 hover:border-slate-300 bg-white'
                      }`}
                    >
                      {/* Step Indicator Node on Timeline */}
                      <span
                        className={`absolute -left-[27px] top-4 w-3.5 h-3.5 rounded-full ring-4 ring-white ${
                          isStCompleted
                            ? 'bg-emerald-500'
                            : isStRunning
                            ? 'bg-blue-500 animate-ping'
                            : isStFailed
                            ? 'bg-rose-500'
                            : 'bg-slate-300'
                        }`}
                      />

                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-800">{st.name}</span>
                          {st.agent_slug && (
                            <span className="px-1.5 py-0.2 rounded bg-purple-50 text-purple-700 border border-purple-200 font-mono text-[10px]">
                              {st.agent_slug}
                            </span>
                          )}
                        </div>

                        <StatusBadge status={st.status} />
                      </div>

                      <p className="text-xs text-slate-500 mt-1 leading-normal">{st.description}</p>

                      {st.output && st.output.summary && (
                        <div className="mt-2.5 p-2.5 rounded bg-slate-50 border border-slate-100 text-[11px] text-slate-700">
                          <span className="font-semibold text-slate-900 block mb-0.5">Summary:</span>
                          {st.output.summary}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Column: Step Output Inspector (5 cols) */}
          <div className="lg:col-span-5">
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs sticky top-20">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-brand-600" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Step Output Payload
                  </h3>
                </div>
                {selectedSubtask && (
                  <span className="font-mono text-[10px] text-slate-400">
                    agent: {selectedSubtask.agent_slug || 'system'}
                  </span>
                )}
              </div>

              {selectedSubtask ? (
                <div className="space-y-3">
                  <div>
                    <span className="text-[11px] font-bold text-slate-600 block mb-1">Subtask:</span>
                    <p className="text-xs font-semibold text-slate-800">{selectedSubtask.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{selectedSubtask.description}</p>
                  </div>

                  <div>
                    <span className="text-[11px] font-bold text-slate-600 block mb-1">Status:</span>
                    <StatusBadge status={selectedSubtask.status} />
                  </div>

                  {selectedSubtask.output ? (
                    <div>
                      <span className="text-[11px] font-bold text-slate-600 block mb-1">Structured Result:</span>
                      <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg text-[11px] font-mono overflow-x-auto max-h-96 leading-relaxed">
                        {JSON.stringify(selectedSubtask.output, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <div className="p-6 text-center text-xs text-slate-400 bg-slate-50 rounded-lg border border-slate-100">
                      Step execution in progress or pending...
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-slate-400">
                  Select a workflow step from the left to inspect its output.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Deliverable Tab */}
      {activeTab === 'deliverable' && isCompleted && (
        <FinalResultView task={task} onOpenRevision={() => setIsRevisionOpen(true)} />
      )}

      {/* Step Inspector Tab */}
      {activeTab === 'inspector' && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-6">
          <h3 className="text-sm font-bold text-slate-900">Execution Plan & Agent Architecture</h3>
          <p className="text-xs text-slate-500">
            Decomposed subtasks, inter-agent dependencies, and raw execution state
          </p>

          <div className="p-4 bg-slate-900 text-emerald-400 rounded-xl font-mono text-xs overflow-x-auto max-h-[500px]">
            {JSON.stringify(
              {
                taskId: task.id,
                status: task.status,
                execution_plan: task.execution_plan,
                executions: executions,
              },
              null,
              2
            )}
          </div>
        </div>
      )}

      {/* Audit Trail Tab */}
      {activeTab === 'audit' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Task Specific Audit Ledger</h3>
            <span className="text-xs text-slate-500">{auditLogs.length} events logged</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[11px] font-semibold">
                <tr>
                  <th className="px-5 py-3">Timestamp</th>
                  <th className="px-4 py-3">Event Type</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Agent / User</th>
                  <th className="px-4 py-3">Risk Level</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="px-5 py-3 font-mono text-slate-500 text-[11px]">
                      {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-800">
                      {log.event_type}
                    </td>
                    <td className="px-4 py-3 text-slate-700">
                      {log.action}
                    </td>
                    <td className="px-4 py-3 font-mono text-slate-500">
                      {log.agent_slug ? `agent:${log.agent_slug}` : log.user_name || 'system'}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase border bg-slate-50 text-slate-600 border-slate-200">
                        {log.risk_level || 'low'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Revision Modal */}
      {isRevisionOpen && (
        <RevisionModal
          isOpen={isRevisionOpen}
          onClose={() => setIsRevisionOpen(false)}
          taskId={task.id}
          onRevisionStarted={() => {
            fetchTaskDetails();
            refreshStats();
          }}
        />
      )}
    </div>
  );
}
