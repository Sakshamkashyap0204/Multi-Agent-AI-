from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.database import get_db
from models.db_models import Approval, ApprovalStatus, Task, TaskStatus
from api.auth import get_current_active_user
from models.db_models import User
from services.audit import log_event
from services.websocket_manager import manager

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalAction(BaseModel):
    notes: Optional[str] = None


def approval_to_dict(a: Approval) -> dict:
    return {
        "id": a.id,
        "task_id": a.task_id,
        "task_name": a.task.name if a.task else None,
        "agent_slug": a.agent_slug,
        "requested_action": a.requested_action,
        "reason": a.reason,
        "risk_level": a.risk_level,
        "agent_output": a.agent_output,
        "policy_triggered": a.policy_triggered,
        "status": a.status.value,
        "reviewer_id": a.reviewer_id,
        "reviewer_name": a.reviewer.full_name if a.reviewer else None,
        "reviewer_notes": a.reviewer_notes,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
    }


@router.get("")
async def list_approvals(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Approval).options(selectinload(Approval.task), selectinload(Approval.reviewer))
    if status:
        query = query.where(Approval.status == ApprovalStatus(status))
    query = query.order_by(Approval.created_at.desc())
    result = await db.execute(query)
    approvals = result.scalars().all()
    return [approval_to_dict(a) for a in approvals]


@router.get("/{approval_id}")
async def get_approval(
    approval_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Approval)
        .options(selectinload(Approval.task), selectinload(Approval.reviewer))
        .where(Approval.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval_to_dict(approval)


async def _resolve_approval(
    approval_id: str,
    new_status: ApprovalStatus,
    notes: str,
    current_user: User,
    db: AsyncSession
):
    result = await db.execute(
        select(Approval)
        .options(selectinload(Approval.task))
        .where(Approval.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != ApprovalStatus.pending:
        raise HTTPException(status_code=400, detail="Approval already resolved")

    approval.status = new_status
    approval.reviewer_id = current_user.id
    approval.reviewer_notes = notes
    approval.resolved_at = datetime.utcnow()
    await db.commit()

    event_map = {
        ApprovalStatus.approved: ("approval_granted", "Approval granted", "low"),
        ApprovalStatus.rejected: ("approval_rejected", "Approval rejected", "medium"),
        ApprovalStatus.changes_requested: ("changes_requested", "Changes requested", "medium"),
    }
    event_type, action, risk = event_map.get(new_status, ("approval_resolved", "Approval resolved", "low"))

    await log_event(
        db, event_type, action,
        task_id=approval.task_id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        agent_slug=approval.agent_slug,
        risk_level=risk,
        details={"approval_id": approval_id, "notes": notes}
    )

    await manager.broadcast(f"task:{approval.task_id}", {
        "type": "approval_resolved",
        "approval_id": approval_id,
        "status": new_status.value,
        "reviewer": current_user.full_name,
    })

    return approval_to_dict(approval)


@router.post("/{approval_id}/approve")
async def approve(
    approval_id: str,
    body: ApprovalAction = ApprovalAction(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await _resolve_approval(approval_id, ApprovalStatus.approved, body.notes or "", current_user, db)


@router.post("/{approval_id}/reject")
async def reject(
    approval_id: str,
    body: ApprovalAction = ApprovalAction(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await _resolve_approval(approval_id, ApprovalStatus.rejected, body.notes or "", current_user, db)


@router.post("/{approval_id}/request-changes")
async def request_changes(
    approval_id: str,
    body: ApprovalAction = ApprovalAction(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await _resolve_approval(approval_id, ApprovalStatus.changes_requested, body.notes or "", current_user, db)
