from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from models.database import get_db
from models.db_models import GovernancePolicy, GovernanceEvent, PolicyAction, PolicySeverity
from api.auth import get_current_active_user
from models.db_models import User

router = APIRouter(prefix="/governance", tags=["governance"])


class PolicyCreate(BaseModel):
    name: str
    description: str
    category: str
    severity: str = "medium"
    trigger: str
    action: str = "require_approval"
    config: dict = {}


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    severity: Optional[str] = None
    action: Optional[str] = None
    config: Optional[dict] = None


def policy_to_dict(p: GovernancePolicy) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "category": p.category,
        "is_active": p.is_active,
        "severity": p.severity.value,
        "trigger": p.trigger,
        "action": p.action.value,
        "config": p.config or {},
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.get("/policies")
async def list_policies(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(GovernancePolicy).order_by(GovernancePolicy.name))
    policies = result.scalars().all()
    return [policy_to_dict(p) for p in policies]


@router.post("/policies")
async def create_policy(
    body: PolicyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    policy = GovernancePolicy(
        name=body.name,
        description=body.description,
        category=body.category,
        severity=PolicySeverity(body.severity),
        trigger=body.trigger,
        action=PolicyAction(body.action),
        config=body.config,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy_to_dict(policy)


@router.patch("/policies/{policy_id}")
async def update_policy(
    policy_id: str,
    body: PolicyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    result = await db.execute(select(GovernancePolicy).where(GovernancePolicy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if body.name is not None:
        policy.name = body.name
    if body.description is not None:
        policy.description = body.description
    if body.is_active is not None:
        policy.is_active = body.is_active
    if body.severity is not None:
        policy.severity = PolicySeverity(body.severity)
    if body.action is not None:
        policy.action = PolicyAction(body.action)
    if body.config is not None:
        policy.config = body.config

    await db.commit()
    await db.refresh(policy)
    return policy_to_dict(policy)


@router.get("/events")
async def list_events(
    task_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy.orm import selectinload
    query = select(GovernanceEvent).options(selectinload(GovernanceEvent.policy))
    if task_id:
        query = query.where(GovernanceEvent.task_id == task_id)
    query = query.order_by(GovernanceEvent.created_at.desc()).limit(100)
    result = await db.execute(query)
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "policy_id": e.policy_id,
            "policy_name": e.policy.name if e.policy else None,
            "task_id": e.task_id,
            "agent_slug": e.agent_slug,
            "event_type": e.event_type,
            "description": e.description,
            "action_taken": e.action_taken,
            "resolved": e.resolved,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
