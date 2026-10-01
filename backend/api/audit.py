from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from models.database import get_db
from models.db_models import AuditLog
from api.auth import get_current_active_user
from models.db_models import User

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
async def list_audit_logs(
    task_id: Optional[str] = None,
    agent_slug: Optional[str] = None,
    event_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLog)
    if task_id:
        query = query.where(AuditLog.task_id == task_id)
    if agent_slug:
        query = query.where(AuditLog.agent_slug == agent_slug)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if risk_level:
        query = query.where(AuditLog.risk_level == risk_level)
    if search:
        query = query.where(AuditLog.action.ilike(f"%{search}%"))

    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "task_id": l.task_id,
            "user_id": l.user_id,
            "user_name": l.user_name,
            "agent_slug": l.agent_slug,
            "event_type": l.event_type,
            "action": l.action,
            "result": l.result,
            "risk_level": l.risk_level,
            "details": l.details,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
