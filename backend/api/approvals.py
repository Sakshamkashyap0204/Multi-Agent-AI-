from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.database import get_db, serialize_doc, MongoModel
from api.auth import get_current_active_user
from services.audit import log_event
from services.websocket_manager import manager

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalAction(BaseModel):
    notes: Optional[str] = None


@router.get("")
async def list_approvals(
    status: Optional[str] = None,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    query = {}
    if status:
        query["status"] = status
    cursor = db.approvals.find(query).sort("created_at", -1)
    approvals = await cursor.to_list(100)
    return [serialize_doc(a) for a in approvals]


@router.get("/{approval_id}")
async def get_approval(
    approval_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    approval = await db.approvals.find_one({"_id": approval_id})
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return serialize_doc(approval)


async def _resolve_approval(
    approval_id: str,
    new_status: str,
    notes: str,
    current_user: MongoModel,
    db
):
    approval = await db.approvals.find_one({"_id": approval_id})
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Approval already resolved")

    now = datetime.utcnow()
    await db.approvals.update_one(
        {"_id": approval_id},
        {"$set": {
            "status": new_status,
            "reviewer_id": current_user.id,
            "reviewer_name": current_user.get("full_name", "Authorized Executive"),
            "reviewer_notes": notes,
            "resolved_at": now,
        }}
    )

    event_map = {
        "approved": ("approval_granted", "Approval granted", "low"),
        "rejected": ("approval_rejected", "Approval rejected", "medium"),
        "changes_requested": ("changes_requested", "Changes requested", "medium"),
    }
    event_type, action, risk = event_map.get(new_status, ("approval_resolved", "Approval resolved", "low"))

    await log_event(
        db, event_type, action,
        task_id=approval.get("task_id"),
        user_id=current_user.id,
        user_name=current_user.get("full_name"),
        agent_slug=approval.get("agent_slug"),
        risk_level=risk,
        details={"approval_id": approval_id, "notes": notes}
    )

    task_id = approval.get("task_id")
    if task_id:
        await manager.broadcast(f"task:{task_id}", {
            "type": "approval_resolved",
            "approval_id": approval_id,
            "status": new_status,
            "reviewer": current_user.get("full_name"),
        })

    updated = await db.approvals.find_one({"_id": approval_id})
    return serialize_doc(updated)


@router.post("/{approval_id}/approve")
async def approve(
    approval_id: str,
    body: ApprovalAction = ApprovalAction(),
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    return await _resolve_approval(approval_id, "approved", body.notes or "", current_user, db)


@router.post("/{approval_id}/reject")
async def reject(
    approval_id: str,
    body: ApprovalAction = ApprovalAction(),
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    return await _resolve_approval(approval_id, "rejected", body.notes or "", current_user, db)


@router.post("/{approval_id}/request-changes")
async def request_changes(
    approval_id: str,
    body: ApprovalAction = ApprovalAction(),
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    return await _resolve_approval(approval_id, "changes_requested", body.notes or "", current_user, db)
