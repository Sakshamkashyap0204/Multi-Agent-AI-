import os
import uuid
from datetime import datetime
import certifi
from motor.motor_asyncio import AsyncIOMotorClient

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://strange0204_db_user:Saksham2302@cluster0.2lys18r.mongodb.net/?appName=Cluster0"
)
DATABASE_NAME = os.getenv("DATABASE_NAME", "orchestrate_ai")

# Configure Motor client with TLS CA certificate for Atlas connections
client_kwargs = {
    "serverSelectionTimeoutMS": 5000,
}
if "mongodb+srv://" in MONGODB_URI:
    client_kwargs["tlsCAFile"] = certifi.where()

client = AsyncIOMotorClient(MONGODB_URI, **client_kwargs)
db = client[DATABASE_NAME]


def gen_id() -> str:
    return str(uuid.uuid4())


class MongoModel(dict):
    """
    Dict wrapper providing attribute-access and automatic .id -> _id resolution.
    Allows seamlessly using doc.status, doc.name, doc.id, and doc["status"].
    """
    def __getattr__(self, key):
        if key == "id":
            return self.get("_id")
        if key in self:
            val = self[key]
            if isinstance(val, dict) and not isinstance(val, MongoModel):
                return MongoModel(val)
            return val
        return None

    def __setattr__(self, key, value):
        if key == "id":
            self["_id"] = value
        else:
            self[key] = value


def serialize_doc(doc) -> dict:
    if not doc:
        return None
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d["_id"])
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
        elif hasattr(v, "value"):
            d[k] = v.value
    return d


async def get_db():
    yield db


async def init_db():
    """Create essential MongoDB indexes for performance and uniqueness."""
    try:
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True)
        await db.agents.create_index("slug", unique=True)
        await db.tasks.create_index("created_at")
        await db.tasks.create_index("status")
        await db.approvals.create_index("task_id")
        await db.approvals.create_index("status")
        await db.audit_logs.create_index([("created_at", -1)])
        await db.audit_logs.create_index("task_id")
        await db.governance_policies.create_index("name", unique=True)
        await db.governance_events.create_index([("created_at", -1)])
        print("[OK] MongoDB Atlas indexes initialized successfully on", DATABASE_NAME)
    except Exception as e:
        print("[WARN] MongoDB index initialization note:", e)
