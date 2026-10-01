from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from models.database import get_db, MongoModel
from api.auth import get_current_active_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
async def get_analytics(
    current_user: MongoModel = Depends(get_current_active_user),
    db=Depends(get_db),
):
    total_tasks = await db.tasks.count_documents({})
    completed_tasks = await db.tasks.count_documents({"status": "COMPLETED"})
    failed_tasks = await db.tasks.count_documents({"status": "FAILED"})
    running_tasks = await db.tasks.count_documents({"status": "RUNNING"})

    agents_cursor = db.agents.find({})
    agents = await agents_cursor.to_list(length=100)
    agent_perf = []
    for a in agents:
        tc = a.get("tasks_completed") or 0
        tf = a.get("tasks_failed") or 0
        total = tc + tf
        total_exec_time = a.get("total_execution_time") or 0.0
        agent_perf.append({
            "name": a.get("name"),
            "slug": a.get("slug"),
            "tasks_completed": tc,
            "tasks_failed": tf,
            "success_rate": round(tc / total * 100, 1) if total > 0 else 0,
            "avg_time": round(total_exec_time / max(tc, 1), 1),
        })

    gov_count = await db.governance_events.count_documents({})
    approvals_granted = await db.audit_logs.count_documents({"event_type": "approval_granted"})
    approvals_requested = await db.audit_logs.count_documents({"event_type": "approval_requested"})

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    trend_tasks = await db.tasks.find({"created_at": {"$gte": thirty_days_ago}}).sort("created_at", 1).to_list(length=1000)

    daily_counts = {}
    for t in trend_tasks:
        cat = t.get("created_at")
        if isinstance(cat, datetime):
            day = cat.strftime("%Y-%m-%d")
        else:
            day = str(cat)[:10] if cat else datetime.utcnow().strftime("%Y-%m-%d")

        if day not in daily_counts:
            daily_counts[day] = {"created": 0, "completed": 0}
        daily_counts[day]["created"] += 1
        if t.get("status") == "COMPLETED":
            daily_counts[day]["completed"] += 1

    trend_data = [
        {"date": day, "created": v["created"], "completed": v["completed"]}
        for day, v in sorted(daily_counts.items())
    ]

    return {
        "summary": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "governance_events": gov_count,
            "approvals_granted": approvals_granted,
            "approvals_requested": approvals_requested,
            "approval_rate": round(approvals_granted / approvals_requested * 100, 1) if approvals_requested > 0 else 0,
        },
        "agent_performance": agent_perf,
        "task_trend": trend_data,
    }
