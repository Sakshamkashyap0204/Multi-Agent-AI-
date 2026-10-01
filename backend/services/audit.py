from datetime import datetime
from models.database import gen_id, MongoModel


async def log_event(
    db,
    event_type: str,
    action: str,
    task_id: str = None,
    user_id: str = None,
    user_name: str = None,
    agent_slug: str = None,
    result: str = None,
    risk_level: str = "low",
    details: dict = None,
) -> MongoModel:
    entry = MongoModel({
        "_id": gen_id(),
        "task_id": task_id,
        "user_id": user_id,
        "user_name": user_name,
        "agent_slug": agent_slug,
        "event_type": event_type,
        "action": action,
        "result": result,
        "risk_level": risk_level,
        "details": details or {},
        "created_at": datetime.utcnow(),
    })
    await db.audit_logs.insert_one(dict(entry))
    return entry


async def create_notification(
    db,
    user_id: str,
    title: str,
    message: str,
    type: str = "info",
    link: str = None,
) -> MongoModel:
    notif = MongoModel({
        "_id": gen_id(),
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": type,
        "link": link,
        "is_read": False,
        "created_at": datetime.utcnow(),
    })
    await db.notifications.insert_one(dict(notif))
    return notif
