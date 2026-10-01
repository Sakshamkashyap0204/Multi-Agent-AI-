from sqlalchemy.ext.asyncio import AsyncSession
from models.db_models import AuditLog, Notification
from datetime import datetime


async def log_event(
    db: AsyncSession,
    event_type: str,
    action: str,
    task_id: str = None,
    user_id: str = None,
    user_name: str = None,
    agent_slug: str = None,
    result: str = None,
    risk_level: str = "low",
    details: dict = None,
):
    entry = AuditLog(
        task_id=task_id,
        user_id=user_id,
        user_name=user_name,
        agent_slug=agent_slug,
        event_type=event_type,
        action=action,
        result=result,
        risk_level=risk_level,
        details=details or {},
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    await db.commit()
    return entry


async def create_notification(
    db: AsyncSession,
    user_id: str,
    title: str,
    message: str,
    type: str = "info",
    link: str = None,
):
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        link=link,
    )
    db.add(notif)
    await db.commit()
    return notif
