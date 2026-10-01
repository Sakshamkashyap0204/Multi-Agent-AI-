import React from 'react';

export function StatusBadge({ status, size = 'sm' }) {
  const s = (status || '').toUpperCase();
  
  let styles = 'bg-slate-100 text-slate-700 border-slate-200';
  let dot = 'bg-slate-400';
  let pulse = false;

  switch (s) {
    case 'RUNNING':
    case 'PLANNING':
      styles = 'bg-blue-50 text-blue-700 border-blue-200';
      dot = 'bg-blue-500';
      pulse = true;
      break;
    case 'WAITING_FOR_APPROVAL':
    case 'WAITING':
      styles = 'bg-amber-50 text-amber-800 border-amber-300 font-semibold';
      dot = 'bg-amber-500';
      pulse = true;
      break;
    case 'COMPLETED':
      styles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      dot = 'bg-emerald-500';
      break;
    case 'FAILED':
      styles = 'bg-rose-50 text-rose-700 border-rose-200';
      dot = 'bg-rose-500';
      break;
    case 'PAUSED':
      styles = 'bg-purple-50 text-purple-700 border-purple-200';
      dot = 'bg-purple-500';
      break;
    case 'REVISION_REQUIRED':
      styles = 'bg-orange-50 text-orange-700 border-orange-200';
      dot = 'bg-orange-500';
      break;
    case 'CANCELLED':
      styles = 'bg-slate-100 text-slate-600 border-slate-300';
      dot = 'bg-slate-400';
      break;
    default:
      styles = 'bg-slate-50 text-slate-700 border-slate-200';
      dot = 'bg-slate-400';
  }

  const label = s.replace(/_/g, ' ');

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium tracking-tight ${styles}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dot} ${pulse ? 'animate-pulse' : ''}`} />
      {label}
    </span>
  );
}

export function PriorityBadge({ priority }) {
  const p = (priority || 'medium').toLowerCase();
  
  let styles = 'bg-slate-100 text-slate-700 border-slate-200';
  switch (p) {
    case 'critical':
      styles = 'bg-rose-100 text-rose-800 border-rose-300 font-semibold';
      break;
    case 'high':
      styles = 'bg-amber-100 text-amber-800 border-amber-300';
      break;
    case 'medium':
      styles = 'bg-blue-50 text-blue-700 border-blue-200';
      break;
    case 'low':
      styles = 'bg-slate-100 text-slate-600 border-slate-200';
      break;
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wide border ${styles}`}>
      {p}
    </span>
  );
}

export function SeverityBadge({ severity }) {
  const s = (severity || 'medium').toLowerCase();
  let styles = 'bg-slate-100 text-slate-700 border-slate-200';
  switch (s) {
    case 'critical':
      styles = 'bg-red-50 text-red-700 border-red-200 font-semibold';
      break;
    case 'high':
      styles = 'bg-orange-50 text-orange-700 border-orange-200';
      break;
    case 'medium':
      styles = 'bg-yellow-50 text-yellow-800 border-yellow-200';
      break;
    case 'low':
      styles = 'bg-slate-50 text-slate-600 border-slate-200';
      break;
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium capitalize border ${styles}`}>
      {s}
    </span>
  );
}

export function ActionBadge({ action }) {
  const a = (action || 'require_approval').toLowerCase();
  let styles = 'bg-blue-50 text-blue-700 border-blue-200';
  switch (a) {
    case 'block':
      styles = 'bg-red-50 text-red-700 border-red-200 font-semibold';
      break;
    case 'require_approval':
      styles = 'bg-amber-50 text-amber-800 border-amber-200';
      break;
    case 'warn':
      styles = 'bg-yellow-50 text-yellow-800 border-yellow-200';
      break;
    case 'log_only':
      styles = 'bg-slate-50 text-slate-600 border-slate-200';
      break;
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono border ${styles}`}>
      {a.replace(/_/g, ' ')}
    </span>
  );
}
