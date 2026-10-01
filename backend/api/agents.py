from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from models.database import get_db, serialize_doc, MongoModel
from api.auth import get_current_active_user

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


def agent_to_dict(a: dict) -> dict:
    if not a:
        return {}
    d = serialize_doc(a)
    completed = d.get("tasks_completed") or 0
    failed = d.get("tasks_failed") or 0
    total = completed + failed
    d["success_rate"] = round(completed / total * 100, 1) if total > 0 else 100.0
    d["avg_execution_time"] = round((d.get("total_execution_time") or 0.0) / max(completed, 1), 1)
    return d


@router.get("")
async def list_agents(
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    cursor = db.agents.find().sort("name", 1)
    agents = await cursor.to_list(100)
    return [agent_to_dict(a) for a in agents]


@router.get("/{agent_id}")
async def get_agent(
    agent_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    agent = await db.agents.find_one({"_id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_to_dict(agent)


@router.get("/{agent_id}/executions")
async def get_agent_executions(
    agent_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    cursor = db.agent_executions.find({"$or": [{"agent_id": agent_id}, {"agent_slug": agent_id}]}).sort("started_at", -1).limit(20)
    execs = await cursor.to_list(20)
    return [serialize_doc(e) for e in execs]


@router.patch("/{agent_id}")
async def update_agent(
    agent_id: str,
    body: AgentUpdate,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    update_fields = {k: v for k, v in body.dict().items() if v is not None}
    if not update_fields:
        agent = await db.agents.find_one({"_id": agent_id})
        return agent_to_dict(agent)

    await db.agents.update_one({"_id": agent_id}, {"$set": update_fields})
    agent = await db.agents.find_one({"_id": agent_id})
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent_to_dict(agent)
