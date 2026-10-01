import React, { useState } from 'react';
import {
  Settings,
  Building2,
  Cpu,
  Bell,
  Shield,
  RotateCcw,
  Check,
  Save,
} from 'lucide-react';
import { useApp, SEEDED_USERS } from '../context/AppContext';

export function SettingsPage() {
  const { currentWorkspace, setCurrentWorkspace, currentUser, switchUser } = useApp();
  const [saved, setSaved] = useState(false);

  const [workspaceSettings, setWorkspaceSettings] = useState({
    name: currentWorkspace,
    timezone: 'UTC (Coordinated Universal Time)',
    governanceMode: 'standard',
  });

  const [aiSettings, setAiSettings] = useState({
    defaultModel: 'gpt-4o-mini',
    temperature: 0.3,
    maxExecutionSteps: 10,
    maxConcurrent: 4,
  });

  const [notifSettings, setNotifSettings] = useState({
    emailAlerts: true,
    approvalAlerts: true,
    failureAlerts: true,
    dailyDigest: false,
  });

  const handleSave = (e) => {
    e.preventDefault();
    setCurrentWorkspace(workspaceSettings.name);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="p-5 rounded-xl bg-white border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Platform Settings</h1>
          <p className="text-xs text-slate-500 mt-1">
            Configure workspace parameters, foundation models, governance defaults, and enterprise access
          </p>
        </div>

        {saved && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
            <Check className="w-4 h-4" />
            <span>Settings Saved</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Workspace Configuration */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Building2 className="w-4 h-4 text-brand-600" />
            <h2 className="text-sm font-bold text-slate-900">Workspace & Tenant Settings</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Workspace Display Name
              </label>
              <input
                type="text"
                value={workspaceSettings.name}
                onChange={(e) =>
                  setWorkspaceSettings({ ...workspaceSettings, name: e.target.value })
                }
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Operational Timezone
              </label>
              <select
                value={workspaceSettings.timezone}
                onChange={(e) =>
                  setWorkspaceSettings({ ...workspaceSettings, timezone: e.target.value })
                }
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="UTC (Coordinated Universal Time)">UTC (Coordinated Universal Time)</option>
                <option value="EST (Eastern Standard Time)">EST (Eastern Standard Time)</option>
                <option value="PST (Pacific Standard Time)">PST (Pacific Standard Time)</option>
                <option value="CET (Central European Time)">CET (Central European Time)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Default Governance Mode for New Tasks
            </label>
            <select
              value={workspaceSettings.governanceMode}
              onChange={(e) =>
                setWorkspaceSettings({ ...workspaceSettings, governanceMode: e.target.value })
              }
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <option value="standard">Standard (Enforce active policies with human checkpoints)</option>
              <option value="strict">Strict (Zero tolerance, all external output requires sign-off)</option>
              <option value="custom">Custom Policy Pipeline</option>
            </select>
          </div>
        </div>

        {/* AI & Orchestration Engine */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Cpu className="w-4 h-4 text-purple-600" />
            <h2 className="text-sm font-bold text-slate-900">AI Model & Orchestrator Configuration</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Default LLM Model
              </label>
              <select
                value={aiSettings.defaultModel}
                onChange={(e) => setAiSettings({ ...aiSettings, defaultModel: e.target.value })}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white font-mono text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <option value="gpt-4o-mini">gpt-4o-mini (Fast, Efficient)</option>
                <option value="gpt-4o">gpt-4o (Deep Reasoning)</option>
                <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Sampling Temperature: {aiSettings.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={aiSettings.temperature}
                onChange={(e) =>
                  setAiSettings({ ...aiSettings, temperature: parseFloat(e.target.value) })
                }
                className="w-full accent-brand-600 mt-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Max Execution Steps (Loop Safeguard)
              </label>
              <input
                type="number"
                min="3"
                max="30"
                value={aiSettings.maxExecutionSteps}
                onChange={(e) =>
                  setAiSettings({ ...aiSettings, maxExecutionSteps: parseInt(e.target.value) || 10 })
                }
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Max Concurrent Specialized Agents
              </label>
              <input
                type="number"
                min="1"
                max="8"
                value={aiSettings.maxConcurrent}
                onChange={(e) =>
                  setAiSettings({ ...aiSettings, maxConcurrent: parseInt(e.target.value) || 4 })
                }
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>
        </div>

        {/* User Directory & Role-Based Access */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Shield className="w-4 h-4 text-emerald-600" />
            <h2 className="text-sm font-bold text-slate-900">User Directory & Role Permissions</h2>
          </div>

          <div className="space-y-2">
            {SEEDED_USERS.map((user) => (
              <div
                key={user.username}
                className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-slate-50/50"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">{user.name}</span>
                    <span className="text-xs text-slate-500 font-mono">@{user.username}</span>
                  </div>
                  <span className="text-[11px] text-slate-500 capitalize">{user.role} · {user.title}</span>
                </div>

                <div className="flex items-center gap-2">
                  {currentUser?.username === user.username ? (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-50 text-brand-700 border border-brand-200 uppercase">
                      Current User
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => switchUser(user.username)}
                      className="px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-100 rounded-md shadow-2xs"
                    >
                      Impersonate
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-3">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Bell className="w-4 h-4 text-amber-600" />
            <h2 className="text-sm font-bold text-slate-900">Notification Preferences</h2>
          </div>

          <div className="space-y-2 pt-1">
            <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={notifSettings.approvalAlerts}
                onChange={(e) =>
                  setNotifSettings({ ...notifSettings, approvalAlerts: e.target.checked })
                }
                className="text-brand-600 focus:ring-brand-500 rounded"
              />
              <span>Immediate In-App Notification when Human Approval is Required</span>
            </label>

            <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={notifSettings.failureAlerts}
                onChange={(e) =>
                  setNotifSettings({ ...notifSettings, failureAlerts: e.target.checked })
                }
                className="text-brand-600 focus:ring-brand-500 rounded"
              />
              <span>High-Priority Alert on Task or Agent Failure</span>
            </label>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            className="flex items-center gap-2 px-5 py-2.5 text-xs font-bold text-white bg-brand-600 hover:bg-brand-700 rounded-lg shadow-xs transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>Save Platform Configuration</span>
          </button>
        </div>
      </form>
    </div>
  );
}
