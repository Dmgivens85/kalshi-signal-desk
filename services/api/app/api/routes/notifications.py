from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.db.models import (
    NotificationDeliveryRecord,
    NotificationEndpoint,
    QuietHourPolicyRecord,
    UserDeviceTargetRecord,
)
from app.services.notifications import NotificationCandidate, NotificationService

router = APIRouter()


class NotificationEndpointCreate(BaseModel):
    channel: str
    destination: str
    title_prefix: str | None = None
    device_target: str | None = None
    provider: str = "pushover"
    filters_json: dict[str, object] = Field(default_factory=dict)
    quiet_hours_enabled: bool = True
    supports_pwa_push: bool = False
    overnight_critical_only: bool = True
    allow_daytime_info: bool = True
    allow_emergency_priority: bool = False
    default_deep_link_base: str | None = None


class NotificationTestRequest(BaseModel):
    title: str
    message: str
    deep_link: str = "/signals/test"
    urgency: str = "standard"
    dedupe_key: str
    overnight_flag: bool = False
    classification: str = "daytime_alert"
    confidence_score: float | None = None


class NotificationPreferencePayload(BaseModel):
    timezone_name: str = "America/New_York"
    quiet_start_hour: int = 22
    quiet_end_hour: int = 7
    allow_critical_overnight: bool = True
    allow_daytime_info: bool = True
    is_enabled: bool = True
    device_name: str | None = None
    destination: str | None = None
    provider: str = "pushover"


@router.get("")
async def list_notifications(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    result = await db.execute(select(NotificationDeliveryRecord).order_by(desc(NotificationDeliveryRecord.created_at)))
    return {"items": [item.to_dict() for item in result.scalars().all()]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_notification_endpoint(
    payload: NotificationEndpointCreate,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    endpoint = NotificationEndpoint(
        user_id=context.subject if context.subject != "anonymous" else None,
        channel=payload.channel,
        destination=payload.destination,
        title_prefix=payload.title_prefix,
        device_target=payload.device_target,
        provider=payload.provider,
        filters_json=payload.filters_json,
        quiet_hours_enabled=payload.quiet_hours_enabled,
        supports_pwa_push=payload.supports_pwa_push,
        overnight_critical_only=payload.overnight_critical_only,
        allow_daytime_info=payload.allow_daytime_info,
        allow_emergency_priority=payload.allow_emergency_priority,
        default_deep_link_base=payload.default_deep_link_base,
    )
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    return endpoint.to_dict()


@router.post("/send")
@router.post("/test")
async def test_notification(
    payload: NotificationTestRequest,
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = NotificationService(settings, db)
    return await service.dispatch_candidate(
        NotificationCandidate(
            title=payload.title,
            message=payload.message,
            deep_link=payload.deep_link,
            urgency=payload.urgency,
            dedupe_key=payload.dedupe_key,
            overnight_flag=payload.overnight_flag,
            classification=payload.classification,
            confidence_score=payload.confidence_score,
        )
    )


@router.get("/preferences")
async def get_preferences(
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    user_id = context.subject if context.subject != "anonymous" else None
    quiet = (
        await db.execute(
            select(QuietHourPolicyRecord)
            .where(QuietHourPolicyRecord.user_id == user_id)
            .order_by(desc(QuietHourPolicyRecord.created_at))
        )
    ).scalar_one_or_none()
    devices = list(
        (
            await db.execute(
                select(UserDeviceTargetRecord)
                .where(UserDeviceTargetRecord.user_id == user_id)
                .order_by(desc(UserDeviceTargetRecord.is_primary), desc(UserDeviceTargetRecord.created_at))
            )
        ).scalars().all()
    )
    return {
        "quiet_hours": quiet.to_dict() if quiet else None,
        "devices": [item.to_dict() for item in devices],
    }


@router.put("/preferences")
async def put_preferences(
    payload: NotificationPreferencePayload,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    user_id = context.subject if context.subject != "anonymous" else None
    quiet = (
        await db.execute(
            select(QuietHourPolicyRecord)
            .where(QuietHourPolicyRecord.user_id == user_id)
            .order_by(desc(QuietHourPolicyRecord.created_at))
        )
    ).scalar_one_or_none()
    if quiet is None:
        quiet = QuietHourPolicyRecord(user_id=user_id)
        db.add(quiet)
    quiet.timezone_name = payload.timezone_name
    quiet.quiet_start_hour = payload.quiet_start_hour
    quiet.quiet_end_hour = payload.quiet_end_hour
    quiet.allow_critical_overnight = payload.allow_critical_overnight
    quiet.allow_daytime_info = payload.allow_daytime_info
    quiet.is_enabled = payload.is_enabled

    device = None
    if payload.device_name and payload.destination:
        device = (
            await db.execute(
                select(UserDeviceTargetRecord).where(
                    UserDeviceTargetRecord.user_id == user_id,
                    UserDeviceTargetRecord.device_name == payload.device_name,
                )
            )
        ).scalar_one_or_none()
        if device is None:
            device = UserDeviceTargetRecord(user_id=user_id, device_name=payload.device_name, destination=payload.destination, provider=payload.provider, is_primary=True)
            db.add(device)
        else:
            device.destination = payload.destination
            device.provider = payload.provider
            device.is_enabled = True
    await db.commit()
    return {
        "quiet_hours": quiet.to_dict(),
        "device": device.to_dict() if device else None,
    }


@router.get("/health")
async def notification_health(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    service = NotificationService(settings, db)
    return await service.health(db)


@router.get("/{notification_id}")
async def get_notification(
    notification_id: str,
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    item = await db.get(NotificationDeliveryRecord, notification_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return item.to_dict()
