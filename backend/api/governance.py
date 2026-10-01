from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.database import get_db, serialize_doc, gen_id, MongoModel
from api.auth import get_current_active_user

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


@router.get("/policies")
async def list_policies(
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    cursor = db.governance_policies.find().sort("name", 1)
    policies = await cursor.to_list(100)
    return [serialize_doc(p) for p in policies]


@router.post("/policies")
async def create_policy(
    body: PolicyCreate,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    policy_doc = {
        "_id": gen_id(),
        "name": body.name,
        "description": body.description,
        "category": body.category,
        "severity": body.severity,
        "trigger": body.trigger,
        "action": body.action,
        "config": body.config or {},
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
    await db.governance_policies.insert_one(policy_doc)
    return serialize_doc(policy_doc)


@router.patch("/policies/{policy_id}")
async def update_policy(
    policy_id: str,
    body: PolicyUpdate,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    update_fields = {k: v for k, v in body.dict().items() if v is not None}
    if not update_fields:
        p = await db.governance_policies.find_one({"_id": policy_id})
        return serialize_doc(p)

    await db.governance_policies.update_one({"_id": policy_id}, {"$set": update_fields})
    policy = await db.governance_policies.find_one({"_id": policy_id})
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return serialize_doc(policy)


@router.get("/events")
async def list_events(
    task_id: Optional[str] = None,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    query = {}
    if task_id:
        query["task_id"] = task_id

    cursor = db.governance_events.find(query).sort("created_at", -1).limit(100)
    events = await cursor.to_list(100)
    return [serialize_doc(e) for e in events]
