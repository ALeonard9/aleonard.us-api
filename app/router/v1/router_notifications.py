# pylint: disable=missing-function-docstring
"""
Per-user notifications.

Read endpoints run the generators first (lazy, idempotent sweep) so a client
always sees current events without any cron in the loop. The same endpoints
serve the web badge today and a mobile app later.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.oauth2 import get_current_user
from app.db.database import get_db
from app.db.models_sandbox import DbNotification
from app.schemas.schemas_sandbox import NotificationResponse, UnreadCountResponse
from app.services.notifications import sweep_all

router = APIRouter(prefix='/v1', tags=['Notifications'])


@router.get('/users/me/notifications', response_model=List[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
    unread_only: bool = False,
    limit: int = 50,
):
    user_pk = current_user[0].pk
    sweep_all(db, user_pk)
    query = db.query(DbNotification).filter(DbNotification.user_id == user_pk)
    if unread_only:
        query = query.filter(DbNotification.read.is_(False))
    return (
        query.order_by(DbNotification.created_at.desc())
        .limit(max(1, min(limit, 200)))
        .all()
    )


@router.get('/users/me/notifications/unread-count', response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    user_pk = current_user[0].pk
    sweep_all(db, user_pk)
    unread = (
        db.query(func.count())  # pylint: disable=not-callable
        .select_from(DbNotification)
        .filter(DbNotification.user_id == user_pk, DbNotification.read.is_(False))
        .scalar()
    )
    return UnreadCountResponse(unread=unread)


@router.put('/users/me/notifications/read-all', response_model=UnreadCountResponse)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    user_pk = current_user[0].pk
    db.query(DbNotification).filter(
        DbNotification.user_id == user_pk, DbNotification.read.is_(False)
    ).update({DbNotification.read: True}, synchronize_session=False)
    db.commit()
    return UnreadCountResponse(unread=0)


@router.put(
    '/users/me/notifications/{notification_id}/read',
    response_model=NotificationResponse,
)
def mark_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    user_pk = current_user[0].pk
    notification = (
        db.query(DbNotification)
        .filter(
            DbNotification.user_id == user_pk,
            DbNotification.id == notification_id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Notification not found'
        )
    notification.read = True
    db.commit()
    db.refresh(notification)
    return notification
