# OrchestrateAI — Enterprise Multi-Agent Operations Platform

**OrchestrateAI** is a production-style enterprise SaaS platform for orchestrating complex business tasks across specialized, autonomous AI agents working collaboratively under strict governance and human-in-the-loop oversight.

---

## 🌟 Key Features

- **Multi-Agent Orchestration**: Dynamic task decomposition and parallel execution graph with dependency resolution (similar to LangGraph concepts).
- **8 Specialized AI Agents**:
  - **Planner Agent**: Understands objectives, maps dependencies, and creates execution plans.
  - **Research Agent**: Collects market sizing, competitive analysis, and external research.
  - **Data Analyst Agent**: Evaluates metric trends, growth rates, and flags anomalies.
  - **Finance Agent**: Models capital allocations, ROI projections, and scenario costs.
  - **Writer Agent**: Compiles comprehensive narrative sections.
  - **Reviewer Agent**: Performs consistency checks and output validation.
  - **Compliance Agent**: Enforces organizational governance policies and flags checkpoints.
  - **Final Synthesis Agent**: Assembles executive deliverables and boardroom presentations.
- **Human-in-the-Loop Oversight**: Intercepts sensitive or high-risk agent actions (e.g. financial proposals > $1M, external publications). Users can Approve, Reject, or Request Changes with reviewer notes.
- **Deterministic Governance Engine**: Active policy catalog (Communication, Finance, Data Privacy, Tool Access, Infinite Loop Safeguards) that actively intervenes in execution.
- **Full Audit Ledger**: Immutable event trail capturing all agent actions, policy triggers, and approval decisions with export to CSV.
- **Real-Time Updates**: WebSockets and responsive polling for live status and agent progress.
- **Enterprise UI**: Built with React 18, Vite, and Tailwind CSS. Features global search (`Ctrl+K`), role switcher, notifications center, and executive report export.

---

## 🏗️ System Architecture

```text
User Request ──► Planner Agent ──► Parallel Execution (Research, Finance, Data)
                                             │
                                             ▼
                                     Writer & Reviewer
                                             │
                                             ▼
                                     Compliance Check
                                             │
                            [Trigger Policy Threshold?]
                                     ├── Yes ──► Human Approval Gate (WAITING_FOR_APPROVAL)
                                     │                  │ (Approved)
                                     └── No  ───────────┴──────────┐
                                                                   ▼
                                                         Final Synthesis Agent
                                                                   │
                                                                   ▼
                                                          Completed Deliverable
                                                          & Immutable Audit Log
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**

---

### 1. Backend Setup

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

- API Server: `http://127.0.0.1:8000`
- Interactive API Docs: `http://127.0.0.1:8000/docs`
- Database: Auto-initializes and seeds SQLite (`orchestrate.db`) on startup.

---

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

- Web Application: `http://127.0.0.1:5173`

---

## 👥 Seeded Enterprise Accounts

| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full governance, agent configurations, audit trail |
| **Manager** | `manager` | `manager123` | Create tasks, review runs, approve/reject checkpoints |
| **Operator** | `operator` | `operator123` | Create tasks, monitor executions, view deliverables |

*(You can also use the Role Switcher dropdown in the top navbar to instantly change roles).*

---

## 📋 End-to-End Verification Test

To run the automated 20-step verification test verifying task creation, multi-agent decomposition, parallel execution, compliance policy interception, human approval, and final synthesis:

```bash
python test_e2e.py
```

---

## 📄 License

Apache-2.0 / MIT.
