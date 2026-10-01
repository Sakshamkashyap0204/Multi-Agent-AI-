import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  CheckCircle2,
  Clock,
  ShieldCheck,
  FileCheck2,
  Cpu,
  RefreshCw,
} from 'lucide-react';
import api from '../services/api';

export function AnalyticsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const res = await api.getAnalytics();
      setData(res);
    } catch (e) {
      console.error('Analytics load error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  if (loading && !data) {
    return (
      <div className="p-12 text-center text-xs text-slate-500 bg-white rounded-xl border border-slate-200">
        Loading analytics metrics...
      </div>
    );
  }

  const summary = data?.summary || {};
  const agentPerf = data?.agent_performance || [];
  const trends = data?.task_trend || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Platform Analytics & Intelligence
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Performance metrics, agent utilization, compliance intervention rate, and throughput trends
          </p>
        </div>

        <button
          onClick={loadAnalytics}
          className="p-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors self-start sm:self-center"
          title="Refresh Metrics"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Completion Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">
            {summary.total_tasks > 0
              ? Math.round((summary.completed_tasks / summary.total_tasks) * 100)
              : 100}
            %
          </p>
          <p className="text-[11px] text-slate-400 mt-1">
            {summary.completed_tasks || 0} of {summary.total_tasks || 0} workflows finalized
          </p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Approval Rate</span>
            <FileCheck2 className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{summary.approval_rate || 100}%</p>
          <p className="text-[11px] text-slate-400 mt-1">
            {summary.approvals_granted || 0} authorizations granted
          </p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Policy Checks</span>
            <ShieldCheck className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{summary.governance_events || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Governance interceptions recorded</p>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Active Fleet</span>
            <Cpu className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-2xl font-bold text-slate-900">{agentPerf.length || 8}</p>
          <p className="text-[11px] text-emerald-600 mt-1 font-medium">100% Agent Availability</p>
        </div>
      </div>

      {/* Task Completion Trends Visual */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Task Velocity & Throughput Trend</h3>
            <p className="text-xs text-slate-500 mt-0.5">Tasks dispatched vs completed over time</p>
          </div>
          <span className="text-xs font-mono text-slate-400">Past 30 Days</span>
        </div>

        {trends.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            No historical throughput data available yet.
          </div>
        ) : (
          <div className="space-y-3 pt-2">
            <div className="h-44 flex items-end gap-3 pt-6 border-b border-slate-200 px-2">
              {trends.map((t, idx) => {
                const maxVal = Math.max(...trends.map((item) => item.created || 1), 5);
                const heightPct = Math.round((t.created / maxVal) * 100);

                return (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1.5 group">
                    <div className="w-full flex items-end justify-center gap-1 h-32">
                      <div
                        style={{ height: `${Math.max(heightPct, 15)}%` }}
                        className="w-full max-w-[28px] bg-brand-500 hover:bg-brand-600 rounded-t transition-all relative"
                        title={`${t.date}: ${t.created} created, ${t.completed} completed`}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 transform -rotate-45 origin-top-left mt-2">
                      {t.date.slice(5)}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="flex items-center justify-center gap-6 pt-2 text-xs text-slate-600">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded bg-brand-500" />
                <span>Tasks Dispatched</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Agent Performance Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200">
          <h3 className="text-sm font-bold text-slate-900">Agent Performance & Utilization</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Success ratios, execution latencies, and workload distribution per agent
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[11px]">
              <tr>
                <th className="px-5 py-3">Agent</th>
                <th className="px-4 py-3">Completed Tasks</th>
                <th className="px-4 py-3">Success Rate</th>
                <th className="px-4 py-3">Avg Latency</th>
                <th className="px-4 py-3">Efficiency Index</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {agentPerf.map((agent) => (
                <tr key={agent.slug} className="hover:bg-slate-50">
                  <td className="px-5 py-3.5 font-sans font-semibold text-slate-900">
                    {agent.name}
                    <span className="block text-[11px] font-mono text-purple-600 font-normal">
                      slug: {agent.slug}
                    </span>
                  </td>

                  <td className="px-4 py-3.5 text-slate-700">{agent.tasks_completed}</td>

                  <td className="px-4 py-3.5">
                    <span className="text-emerald-600 font-bold">{agent.success_rate}%</span>
                  </td>

                  <td className="px-4 py-3.5 text-slate-600">{agent.avg_time}s</td>

                  <td className="px-4 py-3.5">
                    <div className="w-32 bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        style={{ width: `${Math.min(agent.success_rate || 90, 100)}%` }}
                        className="bg-emerald-500 h-full rounded-full"
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
