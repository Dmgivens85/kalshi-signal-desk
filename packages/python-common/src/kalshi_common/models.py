from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    service: str
    status: str
    version: str = "0.1.0"


class HealthCheckResult(BaseModel):
    component: str
    status: str
    detail: str | None = None


class SignalSummary(BaseModel):
    market: str
    thesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    horizon: str
