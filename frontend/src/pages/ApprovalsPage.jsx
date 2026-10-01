import React, { useState, useEffect } from 'react';
import {
  FileCheck2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Clock,
  Shield,
  Layers,
  ArrowRight,
  ExternalLink,
  MessageSquare,
  Sparkles,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../services/api';
import { PriorityBadge } from '../components/common/Badge';

export function ApprovalsPage() {
  const { navigateTo, refreshStats } = useApp();
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [statusFilter, setStatusFilter] = useState('pending'); // 'pending' | 'approved' | 'rejected' | ''
  const [actionNotes, setActionNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const data = await api.getApprovals({ status: statusFilter });
      setApprovals(data || []);
      if (data && data.length > 0 && !selectedApproval) {
        setSelectedApproval(data[0]);
      } else if (data && data.length > 0 && selectedApproval) {
        const found = data.find((a) => a.id === selectedApproval.id);
        setSelectedApproval(found || data[0]);
      }
    } catch (e) {
      console.error('Approvals fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApprovals();
  }, [statusFilter]);

  const handleApprove = async (id) => {
    setActionLoading(true);
    try {
      await api.approve(id, actionNotes || 'Approved by authorized executive.');
      setActionNotes('');
      await loadApprovals();
      refreshStats();
    } catch (e) {
      alert(e.message || 'Approval failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (id) => {
    setActionLoading(true);
    try {
      await api.reject(id, actionNotes || 'Action rejected per compliance review.');
      setActionNotes('');
      await loadApprovals();
      refreshStats();
    } catch (e) {
      alert(e.message || 'Rejection failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRequestChanges = async (id) => {
    if (!actionNotes.trim()) {
      alert('Please enter change instructions in the reviewer notes box.');
      return;
    }
    setActionLoading(true);
    try {
      await api.requestChanges(id, actionNotes);
      setActionNotes('');
      await loadApprovals();
      refreshStats();
    } catch (e) {
      alert(e.message || 'Request changes failed');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Human Oversight & Approvals</h1>
          <p className="text-xs text-slate-500 mt-1">
            Authorizations, sensitive agent actions, and governance verification gates
          </p>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg border border-slate-200 text-xs">
          <button
            onClick={() => setStatusFilter('pending')}
            className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
              statusFilter === 'pending'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Pending
          </button>
          <button
            onClick={() => setStatusFilter('approved')}
            className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
              statusFilter === 'approved'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Approved
          </button>
          <button
            onClick={() => setStatusFilter('rejected')}
            className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
              statusFilter === 'rejected'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Rejected
          </button>
          <button
            onClick={() => setStatusFilter('')}
            className={`px-3 py-1.5 rounded-md font-semibold transition-colors ${
              statusFilter === ''
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All
          </button>
        </div>
      </div>

      {/* Main Approvals Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Approvals List Column (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500 bg-white rounded-xl border border-slate-200">
              Loading approvals...
            </div>
          ) : approvals.length === 0 ? (
            <div className="p-12 text-center bg-white rounded-xl border border-slate-200 shadow-xs">
              <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
              <h3 className="text-sm font-semibold text-slate-800">No Pending Approvals</h3>
              <p className="text-xs text-slate-500 mt-1">
                All agent actions are currently cleared and running within policy parameters.
              </p>
            </div>
          ) : (
            approvals.map((appr) => {
              const isSelected = selectedApproval?.id === appr.id;
              const isPending = appr.status === 'pending';

              return (
                <div
                  key={appr.id}
                  onClick={() => setSelectedApproval(appr)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-brand-500 bg-brand-50/30 shadow-xs ring-1 ring-brand-500/20'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-xs font-bold text-slate-900 truncate">
                      {appr.task_name || 'Autonomous Task Run'}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        appr.risk_level === 'high' || appr.risk_level === 'critical'
                          ? 'bg-rose-100 text-rose-800 border border-rose-200'
                          : 'bg-amber-100 text-amber-800 border border-amber-200'
                      }`}
                    >
                      {appr.risk_level} Risk
                    </span>
                  </div>

                  <p className="text-xs text-slate-700 line-clamp-2 leading-relaxed mb-2 font-medium">
                    {appr.requested_action}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-100 font-mono">
                    <span className="text-purple-700 font-semibold">agent:{appr.agent_slug}</span>
                    <span className="capitalize">{appr.status}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Selected Approval Detail Column (7 cols) */}
        <div className="lg:col-span-7">
          {selectedApproval ? (
            <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 sticky top-20 space-y-5">
              {/* Header */}
              <div className="flex items-start justify-between border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-brand-600 uppercase tracking-wider font-mono">
                      agent: {selectedApproval.agent_slug}
                    </span>
                    <span className="text-slate-300">·</span>
                    <span className="text-xs text-slate-500">
                      Policy: {selectedApproval.policy_triggered || 'Standard Review'}
                    </span>
                  </div>
                  <h2 className="text-base font-bold text-slate-900 mt-1">
                    {selectedApproval.task_name}
                  </h2>
                </div>

                <button
                  onClick={() => navigateTo('run-details', selectedApproval.task_id)}
                  className="flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 bg-brand-50 px-2.5 py-1 rounded-md"
                >
                  <span>Open Task Run</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Proposed Action */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                  Proposed Agent Action
                </h4>
                <p className="text-xs font-semibold text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200">
                  {selectedApproval.requested_action}
                </p>
              </div>

              {/* Justification & Reason */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                  Trigger Reason & Impact
                </h4>
                <p className="text-xs text-slate-700 leading-relaxed bg-amber-50/50 p-3 rounded-lg border border-amber-200">
                  {selectedApproval.reason}
                </p>
              </div>

              {/* Agent Output Payload Preview */}
              {selectedApproval.agent_output && (
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                    Agent Findings & Analysis Context
                  </h4>
                  <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg text-[11px] font-mono overflow-x-auto max-h-56 leading-relaxed">
                    {JSON.stringify(selectedApproval.agent_output, null, 2)}
                  </pre>
                </div>
              )}

              {/* If already resolved, show reviewer feedback */}
              {selectedApproval.status !== 'pending' ? (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                  <span className="font-bold text-slate-900 block mb-1">
                    Resolution Status: <span className="capitalize">{selectedApproval.status}</span>
                  </span>
                  <p className="text-slate-600">
                    Reviewed by: {selectedApproval.reviewer_name || 'System Executive'}
                  </p>
                  {selectedApproval.reviewer_notes && (
                    <p className="text-slate-700 mt-1 italic">
                      "{selectedApproval.reviewer_notes}"
                    </p>
                  )}
                </div>
              ) : (
                /* Decision Action Form */
                <div className="space-y-4 pt-4 border-t border-slate-100">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Reviewer Notes / Directives (Recorded in Audit Ledger)
                    </label>
                    <textarea
                      rows={2}
                      value={actionNotes}
                      onChange={(e) => setActionNotes(e.target.value)}
                      placeholder="Add compliance notes, required modifications, or approval authorization..."
                      className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  <div className="flex flex-wrap items-center justify-end gap-2.5">
                    <button
                      onClick={() => handleRequestChanges(selectedApproval.id)}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-amber-800 bg-amber-50 border border-amber-300 hover:bg-amber-100 rounded-lg transition-colors"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Request Changes</span>
                    </button>

                    <button
                      onClick={() => handleReject(selectedApproval.id)}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-rose-700 bg-white border border-rose-300 hover:bg-rose-50 rounded-lg transition-colors"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Reject Action</span>
                    </button>

                    <button
                      onClick={() => handleApprove(selectedApproval.id)}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-xs transition-colors"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Authorize & Resume Workflow</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-slate-400 bg-white rounded-xl border border-slate-200">
              Select an approval request to review.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
