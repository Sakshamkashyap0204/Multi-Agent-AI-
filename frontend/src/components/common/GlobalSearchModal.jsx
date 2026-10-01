import React, { useState, useEffect } from 'react';
import { Search, X, Layers, Cpu, Activity, ShieldAlert, ArrowRight } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import api from '../../services/api';
import { StatusBadge } from './Badge';

export function GlobalSearchModal({ isOpen, onClose }) {
  const { navigateTo } = useApp();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState({
    tasks: [],
    agents: [],
    auditLogs: [],
    policies: [],
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      setResults({ tasks: [], agents: [], auditLogs: [], policies: [] });
    }
  }, [isOpen]);

  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setResults({ tasks: [], agents: [], auditLogs: [], policies: [] });
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const [tasks, agents, policies, auditLogs] = await Promise.all([
          api.getTasks({ search: query }).catch(() => []),
          api.getAgents().catch(() => []),
          api.getPolicies().catch(() => []),
          api.getAuditLogs({ search: query }).catch(() => []),
        ]);

        const filteredAgents = (agents || []).filter(
          (a) =>
            a.name.toLowerCase().includes(query.toLowerCase()) ||
            a.role.toLowerCase().includes(query.toLowerCase())
        );

        const filteredPolicies = (policies || []).filter(
          (p) =>
            p.name.toLowerCase().includes(query.toLowerCase()) ||
            p.category.toLowerCase().includes(query.toLowerCase())
        );

        setResults({
          tasks: (tasks || []).slice(0, 5),
          agents: filteredAgents.slice(0, 4),
          policies: filteredPolicies.slice(0, 4),
          auditLogs: (auditLogs || []).slice(0, 4),
        });
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  const totalResults =
    results.tasks.length +
    results.agents.length +
    results.policies.length +
    results.auditLogs.length;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 overflow-y-auto">
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs" onClick={onClose} />

      <div className="relative w-full max-w-2xl bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden z-10 animate-in fade-in zoom-in-95 duration-150">
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3 border-b border-slate-200 bg-slate-50/50">
          <Search className="w-5 h-5 text-slate-400 mr-3 shrink-0" />
          <input
            type="text"
            placeholder="Search tasks, agents, governance policies, audit logs..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1 text-slate-400 hover:text-slate-600 mr-1"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <span className="text-[11px] font-mono text-slate-400 px-1.5 py-0.5 rounded border border-slate-200 bg-white">
            ESC
          </span>
        </div>

        {/* Results Body */}
        <div className="max-h-[60vh] overflow-y-auto p-3 divide-y divide-slate-100">
          {loading && (
            <div className="py-8 text-center text-xs text-slate-500">
              Searching across enterprise workspace...
            </div>
          )}

          {!loading && query.length >= 2 && totalResults === 0 && (
            <div className="py-8 text-center">
              <p className="text-sm font-medium text-slate-700">No results found for "{query}"</p>
              <p className="text-xs text-slate-400 mt-1">Try searching for "Market", "Planner", "Finance", or "Policy"</p>
            </div>
          )}

          {!loading && query.length < 2 && (
            <div className="p-4 text-xs text-slate-400">
              <span className="font-semibold text-slate-600 block mb-2">Suggested Quick Searches:</span>
              <div className="flex flex-wrap gap-2">
                {['Market Expansion', 'Compliance', 'Finance Agent', 'External Communication', 'High Risk'].map(
                  (s) => (
                    <button
                      key={s}
                      onClick={() => setQuery(s)}
                      className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs transition-colors"
                    >
                      {s}
                    </button>
                  )
                )}
              </div>
            </div>
          )}

          {/* Tasks Results */}
          {results.tasks.length > 0 && (
            <div className="py-2">
              <div className="px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-blue-500" />
                Tasks ({results.tasks.length})
              </div>
              {results.tasks.map((task) => (
                <button
                  key={task.id}
                  onClick={() => {
                    navigateTo('run-details', task.id);
                    onClose();
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 text-left rounded-lg hover:bg-slate-100 transition-colors group"
                >
                  <div className="min-w-0 pr-3">
                    <p className="text-sm font-medium text-slate-800 truncate group-hover:text-brand-600">
                      {task.name}
                    </p>
                    <p className="text-xs text-slate-500 truncate">{task.goal || task.description}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <StatusBadge status={task.status} />
                    <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-brand-500 group-hover:translate-x-0.5 transition-all" />
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Agents Results */}
          {results.agents.length > 0 && (
            <div className="py-2">
              <div className="px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-purple-500" />
                Agents ({results.agents.length})
              </div>
              {results.agents.map((agent) => (
                <button
                  key={agent.id}
                  onClick={() => {
                    navigateTo('agents');
                    onClose();
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 text-left rounded-lg hover:bg-slate-100 transition-colors group"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800 group-hover:text-brand-600">
                      {agent.name}
                    </p>
                    <p className="text-xs text-slate-500">{agent.role} · Model: {agent.model}</p>
                  </div>
                  <span className="text-xs px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-mono">
                    {agent.slug}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Governance Policies */}
          {results.policies.length > 0 && (
            <div className="py-2">
              <div className="px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
                Governance Policies ({results.policies.length})
              </div>
              {results.policies.map((policy) => (
                <button
                  key={policy.id}
                  onClick={() => {
                    navigateTo('governance');
                    onClose();
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 text-left rounded-lg hover:bg-slate-100 transition-colors group"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800 group-hover:text-brand-600">
                      {policy.name}
                    </p>
                    <p className="text-xs text-slate-500">{policy.category} · Action: {policy.action}</p>
                  </div>
                  <span className="text-xs text-slate-400">{policy.severity}</span>
                </button>
              ))}
            </div>
          )}

          {/* Audit Logs */}
          {results.auditLogs.length > 0 && (
            <div className="py-2">
              <div className="px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-emerald-500" />
                Audit Logs ({results.auditLogs.length})
              </div>
              {results.auditLogs.map((log) => (
                <button
                  key={log.id}
                  onClick={() => {
                    navigateTo('audit');
                    onClose();
                  }}
                  className="w-full flex items-center justify-between px-3 py-2 text-left rounded-lg hover:bg-slate-100 transition-colors group"
                >
                  <div className="min-w-0 pr-2">
                    <p className="text-xs font-medium text-slate-800 truncate group-hover:text-brand-600">
                      {log.action}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      {log.event_type} · {new Date(log.created_at).toLocaleTimeString()}
                    </p>
                  </div>
                  <span className="text-[11px] font-mono text-slate-500 uppercase">{log.risk_level}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
          <span>Search matches Tasks, Agents, Governance Policies & Audit Trail</span>
          <span>Press ESC to exit</span>
        </div>
      </div>
    </div>
  );
}
