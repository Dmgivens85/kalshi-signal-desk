from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.db.models import SignalRecord
from signal_engine.ranking import rank_actionable, rank_overnight
from app.services.signals.engine import SignalEngine

router = APIRouter()


class SignalCreate(BaseModel):
    market_ticker: str
    signal_type: str = "discretionary"
    thesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    horizon: str
    metadata_json: dict[str, object] = Field(default_factory=dict)


@router.get("")
async def list_signals(db: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    result = await db.execute(select(SignalRecord).order_by(SignalRecord.created_at.desc()))
    return {"items": [item.to_dict() for item in result.scalars().all()]}


@router.get("/top")
async def top_signals(db: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    signals = list((await db.execute(select(SignalRecord).order_by(desc(SignalRecord.created_at)))).scalars().all())
    return {"items": [item.to_dict() for item in rank_actionable(signals)[:10]]}


@router.get("/overnight")
async def overnight_signals(db: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    signals = list((await db.execute(select(SignalRecord).order_by(desc(SignalRecord.created_at)))).scalars().all())
    return {"items": [item.to_dict() for item in rank_overnight(signals)[:10]]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_signal(
    payload: SignalCreate,
    context: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    record = SignalRecord(
        market_ticker=payload.market_ticker,
        signal_type=payload.signal_type,
        thesis=payload.thesis,
        confidence=payload.confidence,
        horizon=payload.horizon,
        metadata_json=payload.metadata_json,
        created_by_user_id=context.subject if context.subject != "anonymous" else None,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record.to_dict()


@router.post("/run")
async def run_signal_engine(
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    engine = SignalEngine(settings, db)
    return await engine.run()


@router.get("/{signal_id}")
async def get_signal(signal_id: str, db: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    result = await db.execute(select(SignalRecord).where(SignalRecord.id == signal_id))
    signal = result.scalar_one_or_none()
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal.to_dict()
