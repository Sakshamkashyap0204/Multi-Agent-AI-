from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.database import get_db
from models.db_models import Task, Subtask, AgentExecution, Agent, TaskStatus, TaskPriority, AuditLog, TaskVersion
from api.auth import get_current_active_user
from models.db_models import User
from services.audit import log_event
from services.orchestration import orchestrate_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    goal: Optional[str] = ""
    priority: str = "medium"
    governance_mode: str = "standard"
    human_oversight: str = "approval_for_sensitive"
    deadline: Optional[str] = None


def task_to_dict(task: Task, include_subtasks: bool = False) -> dict:
    d = {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "goal": task.goal,
        "priority": task.priority.value if task.priority else "medium",
        "status": task.status.value if task.status else "CREATED",
        "governance_mode": task.governance_mode,
        "human_oversight": task.human_oversight,
        "current_step": task.current_step,
        "current_agent": task.current_agent,
        "execution_plan": task.execution_plan,
        "final_output": task.final_output,
        "version": task.version,
        "owner_id": task.owner_id,
        "owner_name": task.owner.full_name if task.owner else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "deadline": task.deadline.isoformat() if task.deadline else None,
    }
    if include_subtasks and task.subtasks:
        d["subtasks"] = [subtask_to_dict(s) for s in sorted(task.subtasks, key=lambda x: x.order)]
    return d


def subtask_to_dict(s: Subtask) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "agent_slug": s.agent_slug,
        "status": s.status.value if s.status else "pending",
        "order": s.order,
        "depends_on": s.depends_on or [],
        "output": s.output,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.post("")
async def create_task(
    body: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    deadline = None
    if body.deadline:
        try:
            deadline = datetime.fromisoformat(body.deadline.replace("Z", "+00:00"))
        except Exception:
            pass

    task = Task(
        name=body.name,
        description=body.description,
        goal=body.goal,
        priority=TaskPriority(body.priority),
        governance_mode=body.governance_mode,
        human_oversight=body.human_oversight,
        deadline=deadline,
        owner_id=current_user.id,
        status=TaskStatus.created,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    await log_event(
        db, "task_created", f"Task '{task.name}' created",
        task_id=task.id, user_id=current_user.id, user_name=current_user.full_name,
        risk_level="low", details={"priority": body.priority}
    )

    background_tasks.add_task(orchestrate_task, task.id)

    result = await db.execute(select(Task).where(Task.id == task.id))
    t = result.scalar_one()
    return task_to_dict(t)


@router.get("")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy.orm import selectinload
    query = select(Task).options(selectinload(Task.owner))

    if current_user.role.value == "operator":
        query = query.where(Task.owner_id == current_user.id)

    if status:
        query = query.where(Task.status == TaskStatus(status))
    if priority:
        query = query.where(Task.priority == TaskPriority(priority))
    if search:
        query = query.where(Task.name.ilike(f"%{search}%"))

    query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return [task_to_dict(t) for t in tasks]


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import case
    result = await db.execute(
        select(
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == TaskStatus.running, 1), else_=0)).label("running"),
            func.sum(case((Task.status == TaskStatus.completed, 1), else_=0)).label("completed"),
            func.sum(case((Task.status == TaskStatus.failed, 1), else_=0)).label("failed"),
            func.sum(case((Task.status == TaskStatus.waiting_for_approval, 1), else_=0)).label("waiting"),
            func.sum(case((Task.status == TaskStatus.paused, 1), else_=0)).label("paused"),
        )
    )
    row = result.one()

    agent_result = await db.execute(
        select(func.count(Agent.id)).where(Agent.status == "active")
    )
    active_agents = agent_result.scalar() or 0

    from models.db_models import Approval, ApprovalStatus
    approval_result = await db.execute(
        select(func.count(Approval.id)).where(Approval.status == ApprovalStatus.pending)
    )
    pending_approvals = approval_result.scalar() or 0

    return {
        "total_tasks": row.total or 0,
        "active_tasks": (row.running or 0) + (row.waiting or 0) + (row.paused or 0),
        "running_tasks": row.running or 0,
        "completed_tasks": row.completed or 0,
        "failed_tasks": row.failed or 0,
        "waiting_tasks": row.waiting or 0,
        "active_agents": active_agents,
        "pending_approvals": pending_approvals,
    }


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.owner), selectinload(Task.subtasks))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_dict(task, include_subtasks=True)


@router.get("/{task_id}/executions")
async def get_executions(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AgentExecution)
        .options(selectinload(AgentExecution.agent))
        .where(AgentExecution.task_id == task_id)
        .order_by(AgentExecution.created_at)
    )
    execs = result.scalars().all()
    return [
        {
            "id": e.id,
            "agent_id": e.agent_id,
            "agent_name": e.agent.name if e.agent else e.agent_id,
            "agent_slug": e.agent.slug if e.agent else None,
            "subtask_id": e.subtask_id,
            "status": e.status.value,
            "input_data": e.input_data,
            "output_data": e.output_data,
            "error": e.error,
            "iterations": e.iterations,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "duration": (e.completed_at - e.started_at).total_seconds() if e.completed_at and e.started_at else None,
        }
        for e in execs
    ]


@router.get("/{task_id}/audit")
async def get_task_audit(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.task_id == task_id)
        .order_by(AuditLog.created_at)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "event_type": l.event_type,
            "action": l.action,
            "agent_slug": l.agent_slug,
            "user_name": l.user_name,
            "result": l.result,
            "risk_level": l.risk_level,
            "details": l.details,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


@router.get("/{task_id}/versions")
async def get_versions(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(TaskVersion).where(TaskVersion.task_id == task_id).order_by(TaskVersion.version)
    )
    versions = result.scalars().all()
    return [
        {
            "id": v.id,
            "version": v.version,
            "final_output": v.final_output,
            "revision_notes": v.revision_notes,
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]


@router.post("/{task_id}/pause")
async def pause_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.paused
    task.updated_at = datetime.utcnow()
    await db.commit()
    await log_event(db, "task_paused", "Task paused", task_id=task_id, user_id=current_user.id, user_name=current_user.full_name)
    return {"status": "paused"}


@router.post("/{task_id}/resume")
async def resume_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.running
    task.updated_at = datetime.utcnow()
    await db.commit()
    await log_event(db, "task_resumed", "Task resumed", task_id=task_id, user_id=current_user.id, user_name=current_user.full_name)
    return {"status": "running"}


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.cancelled
    task.updated_at = datetime.utcnow()
    await db.commit()
    await log_event(db, "task_cancelled", "Task cancelled", task_id=task_id, user_id=current_user.id, user_name=current_user.full_name)
    return {"status": "cancelled"}


@router.post("/{task_id}/revise")
async def request_revision(
    task_id: str,
    body: dict,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.version = (task.version or 1) + 1
    task.status = TaskStatus.created
    task.current_step = None
    task.current_agent = None
    task.updated_at = datetime.utcnow()

    version = TaskVersion(
        task_id=task.id,
        version=task.version - 1,
        final_output=task.final_output,
        revision_notes=body.get("notes", ""),
    )
    db.add(version)
    await db.commit()

    await log_event(
        db, "revision_requested", f"Revision requested: {body.get('notes', '')}",
        task_id=task_id, user_id=current_user.id, user_name=current_user.full_name,
        risk_level="low"
    )

    background_tasks.add_task(orchestrate_task, task.id)
    return {"status": "revision_started", "version": task.version}
