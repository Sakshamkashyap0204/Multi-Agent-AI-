const envApi = import.meta.env?.VITE_API_URL || '';
const API_BASE = envApi
  ? (envApi.endsWith('/api') ? envApi : `${envApi.replace(/\/$/, '')}/api`)
  : '/api';

class ApiClient {
  constructor() {
    this.token = localStorage.getItem('token') || null;
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken() {
    return this.token || localStorage.getItem('token');
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        if (response.status === 401 && !endpoint.includes('/auth/token')) {
          // Token expired or invalid
          console.warn('Session expired or unauthorized');
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  // Auth & Profile
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const res = await fetch(`${API_BASE}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  async getMe() {
    return this.request('/auth/me');
  }

  async getNotifications() {
    return this.request('/auth/notifications');
  }

  async markNotificationRead(id) {
    return this.request(`/auth/notifications/${id}/read`, { method: 'POST' });
  }

  // Tasks
  async getTasks(params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.priority) query.append('priority', params.priority);
    if (params.search) query.append('search', params.search);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/tasks${qs}`);
  }

  async getTaskStats() {
    return this.request('/tasks/stats');
  }

  async getTask(id) {
    return this.request(`/tasks/${id}`);
  }

  async createTask(data) {
    return this.request('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTaskExecutions(id) {
    return this.request(`/tasks/${id}/executions`);
  }

  async getTaskAudit(id) {
    return this.request(`/tasks/${id}/audit`);
  }

  async getTaskVersions(id) {
    return this.request(`/tasks/${id}/versions`);
  }

  async pauseTask(id) {
    return this.request(`/tasks/${id}/pause`, { method: 'POST' });
  }

  async resumeTask(id) {
    return this.request(`/tasks/${id}/resume`, { method: 'POST' });
  }

  async cancelTask(id) {
    return this.request(`/tasks/${id}/cancel`, { method: 'POST' });
  }

  async reviseTask(id, notes) {
    return this.request(`/tasks/${id}/revise`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  // Agents
  async getAgents() {
    return this.request('/agents');
  }

  async getAgent(id) {
    return this.request(`/agents/${id}`);
  }

  async getAgentExecutions(id) {
    return this.request(`/agents/${id}/executions`);
  }

  async updateAgent(id, data) {
    return this.request(`/agents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Approvals
  async getApprovals(params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/approvals${qs}`);
  }

  async getApproval(id) {
    return this.request(`/approvals/${id}`);
  }

  async approve(id, notes = '') {
    return this.request(`/approvals/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  async reject(id, notes = '') {
    return this.request(`/approvals/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  async requestChanges(id, notes = '') {
    return this.request(`/approvals/${id}/request-changes`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  // Governance
  async getPolicies() {
    return this.request('/governance/policies');
  }

  async createPolicy(data) {
    return this.request('/governance/policies', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePolicy(id, data) {
    return this.request(`/governance/policies/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async getGovernanceEvents(taskId = null) {
    const qs = taskId ? `?task_id=${taskId}` : '';
    return this.request(`/governance/events${qs}`);
  }

  // Audit
  async getAuditLogs(params = {}) {
    const query = new URLSearchParams();
    if (params.task_id) query.append('task_id', params.task_id);
    if (params.agent_slug) query.append('agent_slug', params.agent_slug);
    if (params.event_type) query.append('event_type', params.event_type);
    if (params.risk_level) query.append('risk_level', params.risk_level);
    if (params.search) query.append('search', params.search);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/audit-logs${qs}`);
  }

  // Analytics
  async getAnalytics() {
    return this.request('/analytics');
  }
}

export const api = new ApiClient();
export default api;
