from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime
import uuid
import enum


def gen_id():
    return str(uuid.uuid4())


class Base(AsyncAttrs, DeclarativeBase):
    pass


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


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.operator)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    tasks = relationship("Task", back_populates="owner")
    approvals = relationship("Approval", back_populates="reviewer")


class Agent(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(Text)
    role = Column(String, nullable=False)
    status = Column(SAEnum(AgentStatus), default=AgentStatus.active)
    model = Column(String, default="gpt-4o-mini")
    system_prompt = Column(Text)
    capabilities = Column(JSON, default=list)
    allowed_tools = Column(JSON, default=list)
    permissions = Column(JSON, default=dict)
    max_iterations = Column(Integer, default=10)
    requires_approval = Column(Boolean, default=False)
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    total_execution_time = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    executions = relationship("AgentExecution", back_populates="agent")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    description = Column(Text)
    goal = Column(Text)
    priority = Column(SAEnum(TaskPriority), default=TaskPriority.medium)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.created)
    governance_mode = Column(String, default="standard")
    human_oversight = Column(String, default="approval_for_sensitive")
    deadline = Column(DateTime, nullable=True)
    owner_id = Column(String, ForeignKey("users.id"))
    owner = relationship("User", back_populates="tasks")
    current_step = Column(String, nullable=True)
    current_agent = Column(String, nullable=True)
    execution_plan = Column(JSON, nullable=True)
    final_output = Column(JSON, nullable=True)
    version = Column(Integer, default=1)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan")
    executions = relationship("AgentExecution", back_populates="task", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="task", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="task", cascade="all, delete-orphan")
    versions = relationship("TaskVersion", back_populates="task", cascade="all, delete-orphan")


class Subtask(Base):
    __tablename__ = "subtasks"
    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="subtasks")
    name = Column(String, nullable=False)
    description = Column(Text)
    agent_slug = Column(String, nullable=True)
    status = Column(SAEnum(ExecutionStatus), default=ExecutionStatus.pending)
    order = Column(Integer, default=0)
    depends_on = Column(JSON, default=list)
    output = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="executions")
    agent_id = Column(String, ForeignKey("agents.id"))
    agent = relationship("Agent", back_populates="executions")
    subtask_id = Column(String, ForeignKey("subtasks.id"), nullable=True)
    status = Column(SAEnum(ExecutionStatus), default=ExecutionStatus.pending)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    iterations = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Approval(Base):
    __tablename__ = "approvals"
    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="approvals")
    agent_slug = Column(String, nullable=True)
    requested_action = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    risk_level = Column(String, default="medium")
    agent_output = Column(JSON, nullable=True)
    policy_triggered = Column(String, nullable=True)
    status = Column(SAEnum(ApprovalStatus), default=ApprovalStatus.pending)
    reviewer_id = Column(String, ForeignKey("users.id"), nullable=True)
    reviewer = relationship("User", back_populates="approvals")
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class GovernancePolicy(Base):
    __tablename__ = "governance_policies"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    severity = Column(SAEnum(PolicySeverity), default=PolicySeverity.medium)
    trigger = Column(Text, nullable=False)
    action = Column(SAEnum(PolicyAction), default=PolicyAction.require_approval)
    config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    events = relationship("GovernanceEvent", back_populates="policy")


class GovernanceEvent(Base):
    __tablename__ = "governance_events"
    id = Column(String, primary_key=True, default=gen_id)
    policy_id = Column(String, ForeignKey("governance_policies.id"), nullable=True)
    policy = relationship("GovernancePolicy", back_populates="events")
    task_id = Column(String, nullable=True)
    agent_slug = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    description = Column(Text)
    action_taken = Column(String, nullable=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    task = relationship("Task", back_populates="audit_logs")
    user_id = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    agent_slug = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    action = Column(String, nullable=False)
    result = Column(String, nullable=True)
    risk_level = Column(String, default="low")
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskVersion(Base):
    __tablename__ = "task_versions"
    id = Column(String, primary_key=True, default=gen_id)
    task_id = Column(String, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="versions")
    version = Column(Integer, nullable=False)
    final_output = Column(JSON, nullable=True)
    revision_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info")
    link = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
