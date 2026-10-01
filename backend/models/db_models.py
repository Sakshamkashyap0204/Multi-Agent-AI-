import enum
import uuid
from datetime import datetime
from models.database import gen_id, MongoModel, serialize_doc


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    operator = "operator"


class TaskStatus(str, enum.Enum):
    created = "CREATED"
    planning = "PLANNING"
    running = "RUNNING"
    waiting_for_approval = "WAITING_FOR_APPROVAL"
    paused = "PAUSED"
    revision_required = "REVISION_REQUIRED"
    completed = "COMPLETED"
    failed = "FAILED"
    cancelled = "CANCELLED"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AgentStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    disabled = "disabled"


class ExecutionStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"
    waiting = "waiting"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    changes_requested = "changes_requested"


class PolicyAction(str, enum.Enum):
    block = "block"
    require_approval = "require_approval"
    warn = "warn"
    log_only = "log_only"


class PolicySeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# Factory helper models for creating typed Mongo documents
def new_user(email: str, username: str, full_name: str, hashed_password: str, role: str = "operator") -> MongoModel:
    return MongoModel({
        "_id": gen_id(),
        "email": email,
        "username": username,
        "full_name": full_name,
        "hashed_password": hashed_password,
        "role": role,
        "is_active": True,
        "created_at": datetime.utcnow(),
    })


def new_agent(name: str, slug: str, role: str, description: str = "", **kwargs) -> MongoModel:
    d = {
        "_id": gen_id(),
        "name": name,
        "slug": slug,
        "role": role,
        "description": description,
        "status": kwargs.get("status", "active"),
        "model": kwargs.get("model", "gpt-4o-mini"),
        "system_prompt": kwargs.get("system_prompt", ""),
        "capabilities": kwargs.get("capabilities", []),
        "allowed_tools": kwargs.get("allowed_tools", []),
        "permissions": kwargs.get("permissions", {}),
        "max_iterations": kwargs.get("max_iterations", 10),
        "requires_approval": kwargs.get("requires_approval", False),
        "tasks_completed": kwargs.get("tasks_completed", 0),
        "tasks_failed": kwargs.get("tasks_failed", 0),
        "total_execution_time": kwargs.get("total_execution_time", 0.0),
        "created_at": datetime.utcnow(),
    }
    return MongoModel(d)


def new_task(name: str, owner_id: str, description: str = "", goal: str = "", priority: str = "medium", **kwargs) -> MongoModel:
    d = {
        "_id": gen_id(),
        "name": name,
        "description": description,
        "goal": goal,
        "priority": priority,
        "status": "CREATED",
        "governance_mode": kwargs.get("governance_mode", "standard"),
        "human_oversight": kwargs.get("human_oversight", "approval_for_sensitive"),
        "deadline": kwargs.get("deadline"),
        "owner_id": owner_id,
        "owner_name": kwargs.get("owner_name", "System Operator"),
        "current_step": None,
        "current_agent": None,
        "execution_plan": None,
        "final_output": None,
        "version": 1,
        "subtasks": [],
        "started_at": None,
        "completed_at": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    return MongoModel(d)
