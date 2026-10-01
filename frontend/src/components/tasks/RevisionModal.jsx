import React, { useState } from 'react';
import { RotateCcw, AlertCircle } from 'lucide-react';
import { Modal } from '../common/Modal';
import api from '../../services/api';

export function RevisionModal({ isOpen, onClose, taskId, onRevisionStarted }) {
  const [notes, setNotes] = useState(
    'Finance section needs more detail on working capital allocation, and the risk analysis should include operational currency hedging.'
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!notes.trim()) {
      setError('Please provide revision instructions.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await api.reviseTask(taskId, notes);
      onRevisionStarted();
      onClose();
    } catch (err) {
      console.error('Revision failed:', err);
      setError(err.message || 'Failed to submit revision');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Request Task Revision"
      subtitle="Provide targeted feedback to trigger a revised multi-agent pass"
      maxWidth="max-w-lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">
            Revision Instructions & Guidance
          </label>
          <textarea
            rows={4}
            required
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Specify what should be changed, expanded, or recalculated..."
            className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <p className="text-[11px] text-slate-500 mt-1">
            The orchestration engine will preserve previous versions and re-engage the Planner and relevant specialized agents.
          </p>
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-2 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            {loading ? 'Submitting...' : 'Dispatch Revision'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
