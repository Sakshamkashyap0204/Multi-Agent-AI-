from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.database import get_db, serialize_doc, gen_id, MongoModel
from api.auth import get_current_active_user
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


def task_to_dict(task: dict, include_subtasks: bool = True) -> dict:
    if not task:
        return {}
    d = serialize_doc(task)
    if not include_subtasks and "subtasks" in d:
        d.pop("subtasks", None)
    return d


@router.post("")
async def create_task(
    body: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    deadline = None
    if body.deadline:
        try:
            deadline = datetime.fromisoformat(body.deadline.replace("Z", "+00:00"))
        except Exception:
            pass

    task_doc = {
        "_id": gen_id(),
        "name": body.name,
        "description": body.description or "",
        "goal": body.goal or "",
        "priority": body.priority,
        "governance_mode": body.governance_mode,
        "human_oversight": body.human_oversight,
        "deadline": deadline,
        "owner_id": current_user.id,
        "owner_name": current_user.get("full_name", "System Operator"),
        "status": "CREATED",
        "current_step": "Initializing",
        "current_agent": None,
        "execution_plan": None,
        "final_output": None,
        "version": 1,
        "subtasks": [],
        "started_at": None,
        "completed_at": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await db.tasks.insert_one(task_doc)

    await log_event(
        db, "task_created", f"Task '{task_doc['name']}' created",
        task_id=task_doc["_id"], user_id=current_user.id, user_name=current_user.get("full_name"),
        risk_level="low", details={"priority": body.priority}
    )

    background_tasks.add_task(orchestrate_task, task_doc["_id"])
    return task_to_dict(task_doc)


@router.get("")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    query = {}
    if current_user.get("role") == "operator":
        query["owner_id"] = current_user.id

    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if search:
        query["name"] = {"$regex": search, "$options": "i"}

    cursor = db.tasks.find(query).sort("created_at", -1).skip(skip).limit(limit)
    tasks = await cursor.to_list(limit)
    return [task_to_dict(t) for t in tasks]


@router.get("/stats")
async def get_stats(
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    total = await db.tasks.count_documents({})
    running = await db.tasks.count_documents({"status": "RUNNING"})
    completed = await db.tasks.count_documents({"status": "COMPLETED"})
    failed = await db.tasks.count_documents({"status": "FAILED"})
    waiting = await db.tasks.count_documents({"status": "WAITING_FOR_APPROVAL"})
    paused = await db.tasks.count_documents({"status": "PAUSED"})

    active_agents = await db.agents.count_documents({"status": "active"})
    pending_approvals = await db.approvals.count_documents({"status": "pending"})

    return {
        "total_tasks": total,
        "active_tasks": running + waiting + paused,
        "running_tasks": running,
        "completed_tasks": completed,
        "failed_tasks": failed,
        "waiting_tasks": waiting,
        "active_agents": active_agents,
        "pending_approvals": pending_approvals,
    }


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    task = await db.tasks.find_one({"_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_dict(task, include_subtasks=True)


@router.get("/{task_id}/executions")
async def get_executions(
    task_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    cursor = db.agent_executions.find({"task_id": task_id}).sort("started_at", 1)
    execs = await cursor.to_list(100)
    return [serialize_doc(e) for e in execs]


@router.get("/{task_id}/audit")
async def get_task_audit(
    task_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    cursor = db.audit_logs.find({"task_id": task_id}).sort("created_at", 1)
    logs = await cursor.to_list(100)
    return [serialize_doc(l) for l in logs]


@router.get("/{task_id}/versions")
async def get_versions(
    task_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    cursor = db.task_versions.find({"task_id": task_id}).sort("version", 1)
    versions = await cursor.to_list(20)
    return [serialize_doc(v) for v in versions]


@router.post("/{task_id}/pause")
async def pause_task(
    task_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    task = await db.tasks.find_one({"_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.tasks.update_one({"_id": task_id}, {"$set": {"status": "PAUSED", "updated_at": datetime.utcnow()}})
    await log_event(db, "task_paused", "Task paused", task_id=task_id, user_id=current_user.id, user_name=current_user.get("full_name"))
    return {"status": "paused"}


@router.post("/{task_id}/resume")
async def resume_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    task = await db.tasks.find_one({"_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.tasks.update_one({"_id": task_id}, {"$set": {"status": "RUNNING", "updated_at": datetime.utcnow()}})
    await log_event(db, "task_resumed", "Task resumed", task_id=task_id, user_id=current_user.id, user_name=current_user.get("full_name"))
    return {"status": "running"}


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    task = await db.tasks.find_one({"_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.tasks.update_one({"_id": task_id}, {"$set": {"status": "CANCELLED", "updated_at": datetime.utcnow()}})
    await log_event(db, "task_cancelled", "Task cancelled", task_id=task_id, user_id=current_user.id, user_name=current_user.get("full_name"))
    return {"status": "cancelled"}


@router.post("/{task_id}/revise")
async def request_revision(
    task_id: str,
    body: dict,
    background_tasks: BackgroundTasks,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    task = await db.tasks.find_one({"_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_version = (task.get("version") or 1) + 1
    version_doc = {
        "_id": gen_id(),
        "task_id": task_id,
        "version": new_version - 1,
        "final_output": task.get("final_output"),
        "revision_notes": body.get("notes", ""),
        "created_at": datetime.utcnow(),
    }
    await db.task_versions.insert_one(version_doc)

    await db.tasks.update_one(
        {"_id": task_id},
        {"$set": {
            "version": new_version,
            "status": "CREATED",
            "current_step": "Planning Revision",
            "current_agent": None,
            "updated_at": datetime.utcnow(),
        }}
    )

    await log_event(
        db, "revision_requested", f"Revision requested: {body.get('notes', '')}",
        task_id=task_id, user_id=current_user.id, user_name=current_user.get("full_name"),
        risk_level="low"
    )

    background_tasks.add_task(orchestrate_task, task_id)
    return {"status": "revision_started", "version": new_version}
