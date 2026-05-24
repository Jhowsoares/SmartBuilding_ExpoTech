"""Schemas Pydantic — Dispositivos."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.device import DeviceType, DeviceStatus
from app.schemas.base import HateoasLink


class DeviceCreate(BaseModel):
    room_id: uuid.UUID
    device_type: DeviceType
    model: Optional[str] = None
    serial_number: Optional[str] = None
    setpoint_celsius: Optional[float] = Field(None, ge=16.0, le=30.0)
    mqtt_topic: Optional[str] = None
    notes: Optional[str] = None


class DeviceUpdate(BaseModel):
    model: Optional[str] = None
    setpoint_celsius: Optional[float] = Field(None, ge=16.0, le=30.0)
    mqtt_topic: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceControlRequest(BaseModel):
    action: str = Field(..., pattern="^(on|off|setpoint)$",
                        description="Ação: 'on', 'off' ou 'setpoint'")
    value: Optional[float] = Field(None, ge=16.0, le=30.0,
                                   description="Temperatura desejada (obrigatório para setpoint)")


class DeviceResponse(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    device_type: DeviceType
    model: Optional[str] = None
    serial_number: Optional[str] = None
    status: DeviceStatus
    is_active: bool
    power_on: bool
    setpoint_celsius: Optional[float] = None
    mqtt_topic: Optional[str] = None
    notes: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    links: List[HateoasLink] = Field(default_factory=list)

    model_config = {"from_attributes": True}

    @staticmethod
    def build_links(device_id: uuid.UUID) -> List[HateoasLink]:
        base = f"/api/v1/devices/{device_id}"
        return [
            HateoasLink(rel="self", href=base),
            HateoasLink(rel="control", href=f"{base}/control", method="POST"),
            HateoasLink(rel="status", href=f"{base}/status"),
        ]


class DeviceControlResponse(BaseModel):
    status: str
    device_id: uuid.UUID
    action: str
    value: Optional[float] = None
    timestamp: datetime
