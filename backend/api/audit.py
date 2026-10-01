from fastapi import APIRouter, Depends
from typing import Optional
from models.database import get_db, serialize_doc, MongoModel
from api.auth import get_current_active_user

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
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    query = {}
    if task_id:
        query["task_id"] = task_id
    if agent_slug:
        query["agent_slug"] = agent_slug
    if event_type:
        query["event_type"] = event_type
    if risk_level:
        query["risk_level"] = risk_level
    if search:
        query["action"] = {"$regex": search, "$options": "i"}

    cursor = db.audit_logs.find(query).sort("created_at", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(limit)
    return [serialize_doc(l) for l in logs]
