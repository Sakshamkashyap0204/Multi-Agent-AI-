import React, { useState } from 'react';
import { Sparkles, Calendar, Shield, Users, AlertCircle, ArrowRight } from 'lucide-react';
import { Modal } from '../common/Modal';
import { useApp } from '../../context/AppContext';
import api from '../../services/api';

const DEMO_TASK_TEMPLATE = {
  name: 'Prepare Q4 Market Expansion Report',
  description:
    'Analyze the available market information, identify potential expansion opportunities, evaluate risks, summarize financial considerations, and prepare an executive recommendation.',
  goal: 'Deliver a boardroom-ready market expansion report covering market size, financial modeling (ROI/payback), competitive landscape, and regulatory compliance considerations.',
  priority: 'high',
  governance_mode: 'standard',
  human_oversight: 'approval_for_sensitive',
  deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
};

export function NewTaskModal({ isOpen, onClose }) {
  const { navigateTo, refreshStats } = useApp();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    goal: '',
    priority: 'medium',
    governance_mode: 'standard',
    human_oversight: 'approval_for_sensitive',
    deadline: '',
    agent_selection_mode: 'auto',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFillDemo = () => {
    setFormData({
      ...DEMO_TASK_TEMPLATE,
      agent_selection_mode: 'auto',
    });
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('Please provide a task name.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const task = await api.createTask({
        name: formData.name,
        description: formData.description,
        goal: formData.goal,
        priority: formData.priority,
        governance_mode: formData.governance_mode,
        human_oversight: formData.human_oversight,
        deadline: formData.deadline ? new Date(formData.deadline).toISOString() : null,
      });

      refreshStats();
      onClose();
      // Navigate directly to the newly started execution
      navigateTo('run-details', task.id);
    } catch (err) {
      console.error('Failed to create task:', err);
      setError(err.message || 'Failed to initiate task');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create New Enterprise Task"
      subtitle="Define objectives, assign specialized AI agents, and enforce governance rules"
      maxWidth="max-w-2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Demo Template Quick-Fill Banner */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-brand-50 border border-brand-200">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-600 shrink-0" />
            <div>
              <p className="text-xs font-semibold text-brand-900">Preconfigured Demo Scenario</p>
              <p className="text-[11px] text-brand-700">Load the official "Q4 Market Expansion Report" task</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleFillDemo}
            className="px-2.5 py-1 text-xs font-semibold rounded bg-brand-600 hover:bg-brand-700 text-white transition-colors shadow-xs"
          >
            Autofill Demo
          </button>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Task Name */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Task Name <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            required
            placeholder="e.g. Prepare Q4 Market Expansion Report"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
          />
        </div>

        {/* Task Description */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Task Description
          </label>
          <textarea
            rows={3}
            placeholder="Detail the scope, business background, and requirements..."
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
          />
        </div>

        {/* Goal / Expected Output */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Expected Deliverable / Output Goal
          </label>
          <input
            type="text"
            placeholder="e.g. Executive synthesis report with scenario model and risk matrix"
            value={formData.goal}
            onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
            className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
          />
        </div>

        {/* Priority & Deadline Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
            <select
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Priority</option>
              <option value="critical">Critical Priority</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Target Deadline</label>
            <div className="relative">
              <input
                type="date"
                value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>
        </div>

        {/* Governance Mode & Oversight */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Governance Mode
            </label>
            <select
              value={formData.governance_mode}
              onChange={(e) => setFormData({ ...formData, governance_mode: e.target.value })}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="standard">Standard (Enforce Active Policies)</option>
              <option value="strict">Strict (Zero-Tolerance & Full Audit)</option>
              <option value="custom">Custom Configuration</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Human Oversight Level
            </label>
            <select
              value={formData.human_oversight}
              onChange={(e) => setFormData({ ...formData, human_oversight: e.target.value })}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="approval_for_sensitive">Approval for sensitive actions (Recommended)</option>
              <option value="approval_before_final">Approval before final output</option>
              <option value="approval_at_every_stage">Approval at every major stage</option>
              <option value="fully_automatic">Fully automatic (No checkpoints)</option>
            </select>
          </div>
        </div>

        {/* Agent Assignment Selection */}
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
          <label className="block text-xs font-semibold text-slate-800 mb-1">
            Agent Orchestration Mode
          </label>
          <div className="flex gap-4 mt-1">
            <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="radio"
                name="agent_mode"
                checked={formData.agent_selection_mode === 'auto'}
                onChange={() => setFormData({ ...formData, agent_selection_mode: 'auto' })}
                className="text-brand-600 focus:ring-brand-500"
              />
              <span>Automatic Agent Assignment via Planner Agent</span>
            </label>
          </div>
          <p className="text-[11px] text-slate-500 mt-1.5">
            The Planner Agent will automatically decompose this task and orchestrate Research, Data Analyst, Finance, Writer, Reviewer, and Compliance agents.
          </p>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg shadow-xs transition-colors"
          >
            {loading ? 'Initiating Task...' : 'Dispatch Task to Orchestrator'}
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>
    </Modal>
  );
}
