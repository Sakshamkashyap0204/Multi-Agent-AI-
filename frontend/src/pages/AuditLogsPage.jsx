import React, { useState, useEffect } from 'react';
import {
  ScrollText,
  Search,
  Filter,
  Download,
  RefreshCw,
  ExternalLink,
  Shield,
  Activity,
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import api from '../services/api';

export function AuditLogsPage() {
  const { navigateTo } = useApp();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [riskFilter, setRiskFilter] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs({
        search: search || undefined,
        event_type: eventTypeFilter || undefined,
        risk_level: riskFilter || undefined,
      });
      setLogs(data || []);
    } catch (e) {
      console.error('Audit fetch error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [eventTypeFilter, riskFilter]);

  const handleExportCSV = () => {
    if (!logs.length) return;
    const headers = ['Timestamp', 'Event Type', 'Action', 'Agent', 'User', 'Risk Level'];
    const rows = logs.map((l) => [
      l.created_at,
      l.event_type,
      `"${(l.action || '').replace(/"/g, '""')}"`,
      l.agent_slug || '',
      l.user_name || '',
      l.risk_level || 'low',
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `audit_trail_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Enterprise Audit Ledger</h1>
          <p className="text-xs text-slate-500 mt-1">
            Immutable compliance record of every agent dispatch, decision, human approval, and governance event
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadAuditLogs}
            className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            loadAuditLogs();
          }}
          className="flex items-center gap-2 flex-1 min-w-[240px]"
        >
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search audit actions, agents, or parameters..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg"
          >
            Filter
          </button>
        </form>

        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="px-3 py-1.5 text-xs border border-slate-300 rounded-lg bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Event Types</option>
            <option value="task_created">Task Created</option>
            <option value="agent_started">Agent Started</option>
            <option value="agent_completed">Agent Completed</option>
            <option value="approval_requested">Approval Requested</option>
            <option value="approval_granted">Approval Granted</option>
            <option value="governance_triggered">Governance Triggered</option>
            <option value="task_completed">Task Completed</option>
            <option value="task_failed">Task Failed</option>
          </select>

          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="px-3 py-1.5 text-xs border border-slate-300 rounded-lg bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="">All Risk Levels</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-4 py-3">Event Type</th>
                <th className="px-4 py-3">Action Description</th>
                <th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Actor / User</th>
                <th className="px-4 py-3">Risk Level</th>
                <th className="px-4 py-3 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-slate-400">
                    Loading audit ledger entries...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-12 text-center text-slate-400">
                    No audit records match the current filter.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-3.5 font-mono text-[11px] text-slate-500">
                      {new Date(log.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                      <span className="block text-[10px] text-slate-400">
                        {new Date(log.created_at).toLocaleDateString()}
                      </span>
                    </td>

                    <td className="px-4 py-3.5">
                      <span className="font-semibold text-slate-800 font-mono text-[11px]">
                        {log.event_type}
                      </span>
                    </td>

                    <td className="px-4 py-3.5 text-slate-700 max-w-md font-medium">
                      {log.action}
                    </td>

                    <td className="px-4 py-3.5 font-mono text-purple-700">
                      {log.agent_slug ? `agent:${log.agent_slug}` : '—'}
                    </td>

                    <td className="px-4 py-3.5 text-slate-600">
                      {log.user_name || 'Autonomous Engine'}
                    </td>

                    <td className="px-4 py-3.5">
                      <span
                        className={`inline-flex px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          log.risk_level === 'critical'
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : log.risk_level === 'high'
                            ? 'bg-orange-100 text-orange-800 border border-orange-200'
                            : log.risk_level === 'medium'
                            ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                            : 'bg-slate-100 text-slate-600 border border-slate-200'
                        }`}
                      >
                        {log.risk_level || 'low'}
                      </span>
                    </td>

                    <td className="px-4 py-3.5 text-right">
                      {log.task_id ? (
                        <button
                          onClick={() => navigateTo('run-details', log.task_id)}
                          className="px-2 py-1 text-[11px] font-semibold text-brand-600 hover:text-brand-700 rounded hover:bg-brand-50"
                        >
                          View Task
                        </button>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
