from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from models.database import get_db
from models.db_models import Agent, AgentStatus, AgentExecution
from api.auth import get_current_active_user
from models.db_models import User

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    max_iterations: Optional[int] = None
    requires_approval: Optional[bool] = None
    allowed_tools: Optional[list] = None


def agent_to_dict(a: Agent) -> dict:
    total = (a.tasks_completed or 0) + (a.tasks_failed or 0)
    success_rate = round((a.tasks_completed or 0) / total * 100, 1) if total > 0 else 0
    avg_time = round((a.total_execution_time or 0) / (a.tasks_completed or 1), 1)
    return {
        "id": a.id,
        "name": a.name,
        "slug": a.slug,
        "description": a.description,
        "role": a.role,
        "status": a.status.value,
        "model": a.model,
        "system_prompt": a.system_prompt,
        "capabilities": a.capabilities or [],
        "allowed_tools": a.allowed_tools or [],
        "permissions": a.permissions or {},
        "max_iterations": a.max_iterations,
        "requires_approval": a.requires_approval,
        "tasks_completed": a.tasks_completed or 0,
        "tasks_failed": a.tasks_failed or 0,
        "success_rate": success_rate,
        "avg_execution_time": avg_time,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


@router.get("")
async def list_agents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Agent).order_by(Agent.name))
    agents = result.scalars().all()
    return [agent_to_dict(a) for a in agents]


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_to_dict(agent)


@router.get("/{agent_id}/executions")
async def get_agent_executions(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AgentExecution)
        .options(selectinload(AgentExecution.task))
        .where(AgentExecution.agent_id == agent_id)
        .order_by(AgentExecution.created_at.desc())
        .limit(20)
    )
    execs = result.scalars().all()
    return [
        {
            "id": e.id,
            "task_id": e.task_id,
            "task_name": e.task.name if e.task else None,
            "status": e.status.value,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "duration": (e.completed_at - e.started_at).total_seconds() if e.completed_at and e.started_at else None,
        }
        for e in execs
    ]


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: str,
    body: AgentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role.value not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if body.name is not None:
        agent.name = body.name
    if body.description is not None:
        agent.description = body.description
    if body.status is not None:
        agent.status = AgentStatus(body.status)
    if body.model is not None:
        agent.model = body.model
    if body.system_prompt is not None:
        agent.system_prompt = body.system_prompt
    if body.max_iterations is not None:
        agent.max_iterations = body.max_iterations
    if body.requires_approval is not None:
        agent.requires_approval = body.requires_approval
    if body.allowed_tools is not None:
        agent.allowed_tools = body.allowed_tools

    await db.commit()
    await db.refresh(agent)
    return agent_to_dict(agent)
