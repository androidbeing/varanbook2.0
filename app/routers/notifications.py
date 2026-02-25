"""
routers/notifications.py – Push notification enqueue endpoint.

Admins can send targeted push notifications to any member in their tenant.
The notification job is placed on SQS for async delivery via Lambda → FCM.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.profile import NotificationEnqueue
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["Push Notifications"])
_notif_svc = NotificationService()


@router.post(
    "/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a push notification to a specific user",
)
async def enqueue_notification(
    payload: NotificationEnqueue,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> dict:
    """
    Place a push notification on the SQS queue.

    - Loads target user to obtain their FCM token.
    - Admins can only notify users in their own tenant.
    - Returns 202 Accepted immediately; delivery is async.
    """
    # Load target user
    target = await db.get(User, payload.user_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found.")

    # Tenant isolation: admin cannot message users in other tenants
    if target.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=403, detail="Cannot send notifications to users in other tenants."
        )

    if not target.fcm_token:
        raise HTTPException(
            status_code=422,
            detail="Target user has no FCM token registered. Ask them to log in from their device.",
        )

    try:
        message_id = _notif_svc.enqueue(
            user_id=target.id,
            fcm_token=target.fcm_token,
            title=payload.title,
            body=payload.body,
            data=payload.data,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return {
        "status": "queued",
        "sqs_message_id": message_id,
        "target_user_id": str(payload.user_id),
    }


@router.post(
    "/broadcast",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Broadcast a push notification to all active members in the tenant",
)
async def broadcast_notification(
    title: str,
    body: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> dict:
    """
    Sends a push notification to EVERY active member of the current tenant
    who has a registered FCM token.

    Messages are batched in groups of 10 (SQS batch limit).
    """
    result = await db.execute(
        select(User).where(
            User.tenant_id == current_user.tenant_id,
            User.is_active == True,  # noqa: E712
            User.fcm_token.isnot(None),
        )
    )
    users = result.scalars().all()

    if not users:
        return {"status": "no_recipients", "count": 0}

    # Build batch payloads
    jobs = [
        {
            "user_id": u.id,
            "fcm_token": u.fcm_token,
            "title": title,
            "body": body,
        }
        for u in users
    ]

    # Process in batches of 10
    message_ids: list[str] = []
    for i in range(0, len(jobs), 10):
        batch = jobs[i : i + 10]
        ids = _notif_svc.enqueue_bulk(batch)
        message_ids.extend(ids)

    return {
        "status": "queued",
        "recipient_count": len(users),
        "sqs_message_ids": message_ids,
    }
