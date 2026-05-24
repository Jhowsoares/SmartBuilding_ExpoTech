"""Schemas Pydantic V2 para dados de sensores IoT."""

from __future__ import annotations
import enum
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Self

from app.schemas.base import HateoasLink, PaginationMeta


class SensorTipo(str, enum.Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESENCE = "presence"


class SensorStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


_VALOR_RANGES = {
    SensorTipo.TEMPERATURE: (-10.0, 60.0),
    SensorTipo.HUMIDITY: (0.0, 100.0),
    SensorTipo.PRESENCE: (0.0, 1.0),
}


class SensorDataIngest(BaseModel):
    sensor_id: str = Field(..., pattern=r"^sensor-(temperature|humidity|presence)-\d{4}$")
    tipo: SensorTipo
    valor: float
    tick: int = Field(..., ge=0)
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def timestamp_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @model_validator(mode="after")
    def valor_range(self) -> Self:
        lo, hi = _VALOR_RANGES[self.tipo]
        if not (lo <= self.valor <= hi):
            raise ValueError(f"valor={self.valor} fora do range [{lo}, {hi}] para tipo={self.tipo.value}")
        return self


class SensorDataResponse(BaseModel):
    id: int
    sensor_id: str
    tipo: SensorTipo
    valor: float
    tick: int
    timestamp: datetime
    is_anomaly: bool
    received_at: datetime
    links: List[HateoasLink] = Field(default_factory=list)

    @classmethod
    def build(cls, payload: SensorDataIngest, record_id: int,
              is_anomaly: bool, created_at: datetime) -> "SensorDataResponse":
        return cls(
            id=record_id,
            sensor_id=payload.sensor_id,
            tipo=payload.tipo,
            valor=payload.valor,
            tick=payload.tick,
            timestamp=payload.timestamp,
            is_anomaly=is_anomaly,
            received_at=created_at,
            links=[
                HateoasLink(rel="self", href=f"/api/v1/sensors/{payload.sensor_id}", method="GET"),
                HateoasLink(rel="latest", href=f"/api/v1/sensors/{payload.sensor_id}/latest", method="GET"),
                HateoasLink(rel="history", href=f"/api/v1/sensors/{payload.sensor_id}/data", method="GET"),
                HateoasLink(rel="ingest", href="/api/v1/sensors/data", method="POST"),
            ],
        )


class SensorLatestResponse(BaseModel):
    sensor_id: str
    tipo: SensorTipo
    valor: float
    tick: int
    timestamp: datetime
    is_anomaly: bool
    links: List[HateoasLink] = Field(default_factory=list)


class SensorResponse(BaseModel):
    id: str
    tipo: SensorTipo
    status: SensorStatus
    last_seen: Optional[datetime] = None
    links: List[HateoasLink] = Field(default_factory=list)

    @classmethod
    def build_links(cls, sensor_id: str) -> List[HateoasLink]:
        return [
            HateoasLink(rel="self", href=f"/api/v1/sensors/{sensor_id}", method="GET"),
            HateoasLink(rel="latest", href=f"/api/v1/sensors/{sensor_id}/latest", method="GET"),
            HateoasLink(rel="history", href=f"/api/v1/sensors/{sensor_id}/data", method="GET"),
        ]


class SensorListResponse(BaseModel):
    data: List[SensorResponse]
    meta: PaginationMeta
