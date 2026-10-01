from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from models.database import get_db, serialize_doc, MongoModel
from services.auth import authenticate_user, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
) -> MongoModel:
    user = await get_current_user(db, token)
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    role_str = user.get("role", "operator")
    token = create_access_token({"sub": user.id, "role": role_str})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "email": user.get("email"),
            "role": role_str,
        }
    }


@router.get("/me")
async def get_me(current_user: MongoModel = Depends(get_current_active_user)):
    return {
        "id": current_user.id,
        "username": current_user.get("username"),
        "full_name": current_user.get("full_name"),
        "email": current_user.get("email"),
        "role": current_user.get("role", "operator"),
    }


@router.get("/notifications")
async def get_notifications(
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    notifs = await db.notifications.find({"user_id": current_user.id}).sort("created_at", -1).limit(20).to_list(20)
    return [serialize_doc(n) for n in notifs]


@router.post("/notifications/{notif_id}/read")
async def mark_read(
    notif_id: str,
    current_user: MongoModel = Depends(get_current_active_user),
    db = Depends(get_db)
):
    await db.notifications.update_one(
        {"_id": notif_id, "user_id": current_user.id},
        {"$set": {"is_read": True}}
    )
    return {"ok": True}
