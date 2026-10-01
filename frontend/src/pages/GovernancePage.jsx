import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Plus,
  AlertTriangle,
  Lock,
  FileCheck,
  RefreshCw,
  ExternalLink,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../services/api';
import { SeverityBadge, ActionBadge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';

export function GovernancePage() {
  const { currentUser, navigateTo } = useApp();
  const [policies, setPolicies] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newPolicy, setNewPolicy] = useState({
    name: '',
    description: '',
    category: 'Security',
    severity: 'high',
    trigger: '',
    action: 'require_approval',
  });

  const loadGovernanceData = async () => {
    setLoading(true);
    try {
      const [polData, evtData] = await Promise.all([
        api.getPolicies(),
        api.getGovernanceEvents(),
      ]);
      setPolicies(polData || []);
      setEvents(evtData || []);
    } catch (e) {
      console.error('Governance fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGovernanceData();
  }, []);

  const handleTogglePolicy = async (policy) => {
    try {
      await api.updatePolicy(policy.id, { is_active: !policy.is_active });
      setPolicies((prev) =>
        prev.map((p) => (p.id === policy.id ? { ...p, is_active: !p.is_active } : p))
      );
    } catch (e) {
      alert(e.message || 'Failed to toggle policy');
    }
  };

  const handleCreatePolicy = async (e) => {
    e.preventDefault();
    try {
      await api.createPolicy(newPolicy);
      setIsCreateModalOpen(false);
      setNewPolicy({
        name: '',
        description: '',
        category: 'Security',
        severity: 'high',
        trigger: '',
        action: 'require_approval',
      });
      await loadGovernanceData();
    } catch (e) {
      alert(e.message || 'Failed to create policy');
    }
  };

  const isAdmin = currentUser?.role === 'admin';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Enterprise Governance Center</h1>
          <p className="text-xs text-slate-500 mt-1">
            Deterministic rule enforcement, sensitive action interception, and compliance checkpoints
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadGovernanceData}
            className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          {isAdmin && (
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold shadow-xs transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Define New Policy</span>
            </button>
          )}
        </div>
      </div>

      {/* Policies Catalog Grid */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Active Governance Rules & Constraints</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              These policies evaluate agent outputs and actions in real time during orchestration
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {policies.filter((p) => p.is_active).length} of {policies.length} Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
              <tr>
                <th className="px-5 py-3">Policy Name & Trigger</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Enforcement Action</th>
                <th className="px-4 py-3">Status</th>
                {isAdmin && <th className="px-4 py-3 text-right">Toggle</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                    Loading governance policies...
                  </td>
                </tr>
              ) : (
                policies.map((policy) => (
                  <tr key={policy.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-5 py-4 max-w-md">
                      <p className="font-semibold text-slate-900">{policy.name}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">{policy.description}</p>
                      <span className="text-[10px] font-mono text-purple-600 block mt-1">
                        Trigger: {policy.trigger}
                      </span>
                    </td>

                    <td className="px-4 py-4 text-slate-700 font-medium">{policy.category}</td>

                    <td className="px-4 py-4">
                      <SeverityBadge severity={policy.severity} />
                    </td>

                    <td className="px-4 py-4">
                      <ActionBadge action={policy.action} />
                    </td>

                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold ${
                          policy.is_active
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-slate-100 text-slate-500 border border-slate-200'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            policy.is_active ? 'bg-emerald-500' : 'bg-slate-400'
                          }`}
                        />
                        {policy.is_active ? 'Enforced' : 'Disabled'}
                      </span>
                    </td>

                    {isAdmin && (
                      <td className="px-4 py-4 text-right">
                        <button
                          onClick={() => handleTogglePolicy(policy)}
                          className={`px-2.5 py-1 text-xs font-semibold rounded-lg border transition-colors ${
                            policy.is_active
                              ? 'bg-white hover:bg-slate-100 text-slate-700 border-slate-200 shadow-2xs'
                              : 'bg-emerald-600 hover:bg-emerald-700 text-white border-transparent shadow-xs'
                          }`}
                        >
                          {policy.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Governance Interceptions / Events Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <h2 className="text-sm font-bold text-slate-900">Governance Interceptions Log</h2>
          </div>
          <span className="text-xs text-slate-500">{events.length} violations intercepted</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-4 py-3">Policy Triggered</th>
                <th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Interception Description</th>
                <th className="px-4 py-3">Action Taken</th>
                <th className="px-4 py-3 text-right">Resolution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {events.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-slate-400">
                    No governance violations recorded.
                  </td>
                </tr>
              ) : (
                events.map((evt) => (
                  <tr key={evt.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-3.5 font-mono text-[11px] text-slate-500">
                      {new Date(evt.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </td>

                    <td className="px-4 py-3.5 font-semibold text-slate-900">
                      {evt.policy_name || 'System Constraint'}
                    </td>

                    <td className="px-4 py-3.5 font-mono text-purple-700">
                      agent:{evt.agent_slug || 'compliance'}
                    </td>

                    <td className="px-4 py-3.5 text-slate-700 max-w-sm">{evt.description}</td>

                    <td className="px-4 py-3.5">
                      <ActionBadge action={evt.action_taken} />
                    </td>

                    <td className="px-4 py-3.5 text-right">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          evt.resolved
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-amber-50 text-amber-800 border border-amber-200'
                        }`}
                      >
                        {evt.resolved ? 'Authorized' : 'Awaiting Gate'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Define Policy Modal */}
      {isCreateModalOpen && (
        <Modal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          title="Create Governance Policy"
          subtitle="Configure real-time automated constraints on multi-agent execution"
          maxWidth="max-w-lg"
        >
          <form onSubmit={handleCreatePolicy} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Policy Name
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Financial Actions Threshold"
                value={newPolicy.name}
                onChange={(e) => setNewPolicy({ ...newPolicy, name: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Category
              </label>
              <select
                value={newPolicy.category}
                onChange={(e) => setNewPolicy({ ...newPolicy, category: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="Security">Security</option>
                <option value="Finance">Finance</option>
                <option value="Communication">Communication</option>
                <option value="Data">Data Privacy</option>
                <option value="Safety">Safety & Loops</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Policy Description
              </label>
              <textarea
                rows={2}
                required
                placeholder="Describe what this policy protects against..."
                value={newPolicy.description}
                onChange={(e) => setNewPolicy({ ...newPolicy, description: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Severity</label>
                <select
                  value={newPolicy.severity}
                  onChange={(e) => setNewPolicy({ ...newPolicy, severity: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Enforcement Action
                </label>
                <select
                  value={newPolicy.action}
                  onChange={(e) => setNewPolicy({ ...newPolicy, action: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="require_approval">Require Approval</option>
                  <option value="block">Block Action</option>
                  <option value="warn">Warn Only</option>
                  <option value="log_only">Log Only</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Trigger Expression / Condition
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Agent attempts external communication or publication"
                value={newPolicy.trigger}
                onChange={(e) => setNewPolicy({ ...newPolicy, trigger: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono text-xs"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(false)}
                className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-xs"
              >
                Publish Policy
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
