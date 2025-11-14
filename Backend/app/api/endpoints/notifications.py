from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database.session import get_db
from ...database import crud
from ...auth.security import get_current_active_user
from ...schemas.user import User
from ...utils import notifications as notification_utils

router = APIRouter()

@router.get("/notifications/")
async def get_user_notifications(
    unread_only: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notifications = notification_utils.get_user_notifications(
        db, user_id=current_user.id, unread_only=unread_only
    )
    return notifications[skip:skip + limit]

@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notification = notification_utils.mark_notification_as_read(
        db, notification_id=notification_id, user_id=current_user.id
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}