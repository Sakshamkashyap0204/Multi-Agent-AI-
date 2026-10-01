from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from models.database import get_db
from models.db_models import Task, Agent, AgentExecution, AuditLog, GovernanceEvent, TaskStatus, ExecutionStatus
from api.auth import get_current_active_user
from models.db_models import User
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
async def get_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    task_result = await db.execute(
        select(
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == TaskStatus.completed, 1), else_=0)).label("completed"),
            func.sum(case((Task.status == TaskStatus.failed, 1), else_=0)).label("failed"),
            func.sum(case((Task.status == TaskStatus.running, 1), else_=0)).label("running"),
        )
    )
    task_row = task_result.one()

    agent_result = await db.execute(select(Agent))
    agents = agent_result.scalars().all()
    agent_perf = []
    for a in agents:
        total = (a.tasks_completed or 0) + (a.tasks_failed or 0)
        agent_perf.append({
            "name": a.name,
            "slug": a.slug,
            "tasks_completed": a.tasks_completed or 0,
            "tasks_failed": a.tasks_failed or 0,
            "success_rate": round((a.tasks_completed or 0) / total * 100, 1) if total > 0 else 0,
            "avg_time": round((a.total_execution_time or 0) / max(a.tasks_completed or 1, 1), 1),
        })

    gov_result = await db.execute(select(func.count(GovernanceEvent.id)))
    gov_count = gov_result.scalar() or 0

    approval_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.event_type == "approval_granted")
    )
    approvals_granted = approval_result.scalar() or 0

    approval_req_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.event_type == "approval_requested")
    )
    approvals_requested = approval_req_result.scalar() or 0

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    trend_result = await db.execute(
        select(Task)
        .where(Task.created_at >= thirty_days_ago)
        .order_by(Task.created_at)
    )
    trend_tasks = trend_result.scalars().all()

    daily_counts = {}
    for t in trend_tasks:
        day = t.created_at.strftime("%Y-%m-%d")
        if day not in daily_counts:
            daily_counts[day] = {"created": 0, "completed": 0}
        daily_counts[day]["created"] += 1
        if t.status == TaskStatus.completed:
            daily_counts[day]["completed"] += 1

    trend_data = [
        {"date": day, "created": v["created"], "completed": v["completed"]}
        for day, v in sorted(daily_counts.items())
    ]

    return {
        "summary": {
            "total_tasks": task_row.total or 0,
            "completed_tasks": task_row.completed or 0,
            "failed_tasks": task_row.failed or 0,
            "running_tasks": task_row.running or 0,
            "governance_events": gov_count,
            "approvals_granted": approvals_granted,
            "approvals_requested": approvals_requested,
            "approval_rate": round(approvals_granted / approvals_requested * 100, 1) if approvals_requested > 0 else 0,
        },
        "agent_performance": agent_perf,
        "task_trend": trend_data,
    }
