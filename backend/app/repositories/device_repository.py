"""Repositório de Devices."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device, DeviceStatus
from app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, payload: DeviceCreate) -> Device:
        device = Device(
            room_id=payload.room_id,
            device_type=payload.device_type,
            model=payload.model,
            serial_number=payload.serial_number,
            setpoint_celsius=payload.setpoint_celsius,
            mqtt_topic=payload.mqtt_topic,
            notes=payload.notes,
        )
        self._db.add(device)
        await self._db.flush()
        await self._db.refresh(device)
        return device

    async def get_by_id(self, device_id: uuid.UUID) -> Optional[Device]:
        result = await self._db.execute(select(Device).where(Device.id == device_id))
        return result.scalar_one_or_none()

    async def list_devices(self, room_id: Optional[uuid.UUID] = None,
                           status: Optional[DeviceStatus] = None,
                           page: int = 1, size: int = 20) -> Tuple[List[Device], int]:
        q = select(Device).where(Device.is_active.is_(True))
        if room_id:
            q = q.where(Device.room_id == room_id)
        if status:
            q = q.where(Device.status == status)
        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        rows = (await self._db.execute(q.order_by(Device.created_at.desc())
                                        .offset((page - 1) * size).limit(size))).scalars().all()
        return list(rows), total

    async def update(self, device: Device, payload: DeviceUpdate) -> Device:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(device, field, value)
        device.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(device)
        return device

    async def set_power(self, device: Device, power_on: bool) -> Device:
        device.power_on = power_on
        device.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(device)
        return device

    async def set_setpoint(self, device: Device, setpoint: float) -> Device:
        device.setpoint_celsius = setpoint
        device.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(device)
        return device

    async def update_status(self, device: Device, status: DeviceStatus) -> Device:
        device.status = status
        device.last_seen_at = datetime.now(timezone.utc)
        device.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        return device

    async def delete(self, device: Device) -> None:
        device.is_active = False
        device.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
