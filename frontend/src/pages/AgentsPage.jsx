import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Settings2,
  CheckCircle2,
  Clock,
  Wrench,
  Shield,
  Layers,
  Edit3,
  Power,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../services/api';
import { Modal } from '../components/common/Modal';

export function AgentsPage() {
  const { currentUser } = useApp();
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [configuringAgent, setConfiguringAgent] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    status: 'active',
    model: 'gpt-4o-mini',
    system_prompt: '',
    max_iterations: 10,
    requires_approval: false,
  });

  const loadAgents = async () => {
    setLoading(true);
    try {
      const data = await api.getAgents();
      setAgents(data || []);
    } catch (e) {
      console.error('Error fetching agents:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleOpenView = async (agent) => {
    setSelectedAgent(agent);
    try {
      const execData = await api.getAgentExecutions(agent.id);
      setExecutions(execData || []);
    } catch (e) {
      setExecutions([]);
    }
  };

  const handleOpenConfig = (agent) => {
    setConfiguringAgent(agent);
    setEditForm({
      name: agent.name,
      description: agent.description,
      status: agent.status,
      model: agent.model || 'gpt-4o-mini',
      system_prompt: agent.system_prompt || '',
      max_iterations: agent.max_iterations || 10,
      requires_approval: agent.requires_approval || false,
    });
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    if (!configuringAgent) return;
    try {
      await api.updateAgent(configuringAgent.id, editForm);
      setConfiguringAgent(null);
      await loadAgents();
    } catch (err) {
      alert(err.message || 'Failed to update agent configuration');
    }
  };

  const canConfigure = currentUser?.role === 'admin' || currentUser?.role === 'manager';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Specialized Agent Fleet</h1>
          <p className="text-xs text-slate-500 mt-1">
            Autonomous multi-agent registry with runtime capabilities, prompt controls, and tool access limits
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
          <span className="font-semibold text-slate-900">{agents.length}</span> Agents Configured
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? (
          <div className="col-span-full p-12 text-center text-xs text-slate-400 bg-white rounded-xl border border-slate-200">
            Loading agent registry...
          </div>
        ) : (
          agents.map((agent) => (
            <div
              key={agent.id}
              className="bg-white rounded-xl border border-slate-200 shadow-2xs hover:shadow-xs hover:border-slate-300 transition-all p-5 flex flex-col justify-between"
            >
              <div>
                {/* Agent Card Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="w-9 h-9 rounded-lg bg-purple-50 text-purple-700 border border-purple-200 flex items-center justify-center font-bold text-sm shrink-0">
                    <Cpu className="w-5 h-5" />
                  </div>

                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      agent.status === 'active'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-slate-100 text-slate-600 border border-slate-200'
                    }`}
                  >
                    {agent.status}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-900">{agent.name}</h3>
                <span className="text-[11px] font-mono text-purple-600 block mt-0.5">
                  slug: {agent.slug}
                </span>

                <p className="text-xs text-slate-500 mt-2 line-clamp-3 leading-relaxed">
                  {agent.description}
                </p>

                {/* Capabilities Tags */}
                {agent.capabilities && agent.capabilities.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-3">
                    {agent.capabilities.slice(0, 3).map((cap, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[10px] font-medium"
                      >
                        {cap}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Agent Metrics & Actions Footer */}
              <div className="pt-4 mt-4 border-t border-slate-100 space-y-3">
                <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono bg-slate-50 py-2 rounded-lg border border-slate-100">
                  <div>
                    <span className="text-slate-400 block">Tasks</span>
                    <span className="font-bold text-slate-800">{agent.tasks_completed || 0}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Success</span>
                    <span className="font-bold text-emerald-600">
                      {agent.success_rate || 100}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Avg Time</span>
                    <span className="font-bold text-slate-800">
                      {agent.avg_execution_time || 2.1}s
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleOpenView(agent)}
                    className="flex-1 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors text-center"
                  >
                    View Agent
                  </button>

                  {canConfigure && (
                    <button
                      onClick={() => handleOpenConfig(agent)}
                      className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
                      title="Configure Agent instructions & limits"
                    >
                      <Settings2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* View Agent Modal */}
      {selectedAgent && (
        <Modal
          isOpen={Boolean(selectedAgent)}
          onClose={() => setSelectedAgent(null)}
          title={selectedAgent.name}
          subtitle={`Role: ${selectedAgent.role} · Slug: ${selectedAgent.slug}`}
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                Overview & Description
              </h4>
              <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200">
                {selectedAgent.description}
              </p>
            </div>

            {/* Allowed Tools */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                Authorized Tool Integrations
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {(selectedAgent.allowed_tools || []).map((tool, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200 text-xs font-mono font-medium"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>

            {/* System Prompt */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                System Instructions & Prompt Template
              </h4>
              <pre className="p-3 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono overflow-x-auto max-h-48 leading-relaxed whitespace-pre-wrap">
                {selectedAgent.system_prompt || 'Standard multi-agent runner configuration'}
              </pre>
            </div>

            {/* Recent Executions */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Recent Subtask Executions
              </h4>
              {executions.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No logged executions yet.</p>
              ) : (
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {executions.map((e) => (
                    <div
                      key={e.id}
                      className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                    >
                      <span className="font-medium text-slate-800">{e.task_name || 'Subtask'}</span>
                      <div className="flex items-center gap-3 font-mono text-[11px] text-slate-500">
                        <span>{e.duration ? `${e.duration.toFixed(1)}s` : 'done'}</span>
                        <span className="capitalize px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {e.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Configure Agent Modal */}
      {configuringAgent && (
        <Modal
          isOpen={Boolean(configuringAgent)}
          onClose={() => setConfiguringAgent(null)}
          title={`Configure ${configuringAgent.name}`}
          subtitle="Modify agent instructions, LLM model, execution safeguards, and human approval gates"
          maxWidth="max-w-2xl"
        >
          <form onSubmit={handleSaveConfig} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Agent Display Name
                </label>
                <input
                  type="text"
                  required
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Agent Operational Status
                </label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="active">Active (Available for Orchestration)</option>
                  <option value="paused">Paused (Temporarily Suspended)</option>
                  <option value="disabled">Disabled (Cannot be Assigned)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Assigned Foundation Model
                </label>
                <select
                  value={editForm.model}
                  onChange={(e) => setEditForm({ ...editForm, model: e.target.value })}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono text-xs"
                >
                  <option value="gpt-4o-mini">gpt-4o-mini (Default Fast)</option>
                  <option value="gpt-4o">gpt-4o (High Reasoning)</option>
                  <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Max Iteration Steps (Loop Protection)
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={editForm.max_iterations}
                  onChange={(e) =>
                    setEditForm({ ...editForm, max_iterations: parseInt(e.target.value) || 10 })
                  }
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                System Prompt Instructions
              </label>
              <textarea
                rows={5}
                value={editForm.system_prompt}
                onChange={(e) => setEditForm({ ...editForm, system_prompt: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg font-mono focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Agent guidelines must adhere to system-wide governance constraints.
              </p>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-800">
                <input
                  type="checkbox"
                  checked={editForm.requires_approval}
                  onChange={(e) =>
                    setEditForm({ ...editForm, requires_approval: e.target.checked })
                  }
                  className="text-brand-600 focus:ring-brand-500 rounded"
                />
                <span>Mandate Human Authorization Checkpoint Before Submitting Deliverable</span>
              </label>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setConfiguringAgent(null)}
                className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-xs"
              >
                Save Agent Configuration
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
