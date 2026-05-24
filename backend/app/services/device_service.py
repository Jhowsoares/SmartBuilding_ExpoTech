"""Serviço de Devices — casos de uso de CRUD e controle."""
from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device, DeviceStatus
from app.models.command import CommandType, CommandStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.device_repository import DeviceRepository
from app.schemas.device import (
    DeviceCreate, DeviceControlRequest, DeviceControlResponse,
    DeviceResponse, DeviceUpdate,
)
from app.schemas.base import HateoasLink
from app.core.exceptions import ResourceNotFoundError, BusinessRuleError

logger = logging.getLogger(__name__)

# RN03: faixa de setpoint aceitável
_MIN_SETPOINT = 16.0
_MAX_SETPOINT = 30.0
# RN03: faixa ideal sugerida
_IDEAL_MIN = 23.0
_IDEAL_MAX = 25.0


class DeviceService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = DeviceRepository(db)
        self._audit = AuditRepository(db)

    async def create_device(self, payload: DeviceCreate, user_id: str = "system") -> DeviceResponse:
        device = await self._repo.create(payload)
        await self._audit.log(
            action="device_create", user_id=user_id, resource=str(device.id),
            metadata={"device_type": device.device_type.value, "room_id": str(device.room_id)},
        )
        logger.info("Device criado | id=%s tipo=%s room=%s", device.id, device.device_type, device.room_id)
        return self._to_response(device)

    async def list_devices(self, room_id: Optional[uuid.UUID] = None,
                           status: Optional[DeviceStatus] = None,
                           page: int = 1, size: int = 20) -> Tuple[List[DeviceResponse], int]:
        devices, total = await self._repo.list_devices(room_id=room_id, status=status, page=page, size=size)
        return [self._to_response(d) for d in devices], total

    async def get_device(self, device_id: uuid.UUID) -> DeviceResponse:
        device = await self._repo.get_by_id(device_id)
        if not device or not device.is_active:
            raise ResourceNotFoundError("Device", str(device_id))
        return self._to_response(device)

    async def update_device(self, device_id: uuid.UUID, payload: DeviceUpdate,
                            user_id: str = "system") -> DeviceResponse:
        device = await self._repo.get_by_id(device_id)
        if not device or not device.is_active:
            raise ResourceNotFoundError("Device", str(device_id))
        device = await self._repo.update(device, payload)
        await self._audit.log(
            action="device_update", user_id=user_id, resource=str(device_id),
            metadata=payload.model_dump(exclude_unset=True),
        )
        return self._to_response(device)

    async def delete_device(self, device_id: uuid.UUID, user_id: str = "system") -> None:
        device = await self._repo.get_by_id(device_id)
        if not device or not device.is_active:
            raise ResourceNotFoundError("Device", str(device_id))
        await self._repo.delete(device)
        await self._audit.log(action="device_delete", user_id=user_id, resource=str(device_id), metadata={})

    async def control_device(self, device_id: uuid.UUID,
                              payload: DeviceControlRequest,
                              user_id: str = "system") -> DeviceControlResponse:
        device = await self._repo.get_by_id(device_id)
        if not device or not device.is_active:
            raise ResourceNotFoundError("Device", str(device_id))

        now = datetime.now(timezone.utc)

        if payload.action == "on":
            device = await self._repo.set_power(device, True)
            cmd_type = CommandType.POWER_ON
        elif payload.action == "off":
            device = await self._repo.set_power(device, False)
            cmd_type = CommandType.POWER_OFF
        elif payload.action == "setpoint":
            if payload.value is None:
                raise BusinessRuleError("Informe o valor do setpoint para ação 'setpoint'.")
            if not (_MIN_SETPOINT <= payload.value <= _MAX_SETPOINT):
                raise BusinessRuleError(
                    f"Setpoint fora da faixa permitida ({_MIN_SETPOINT}–{_MAX_SETPOINT}°C)."
                )
            device = await self._repo.set_setpoint(device, payload.value)
            cmd_type = CommandType.SET_TEMPERATURE
        else:
            raise BusinessRuleError(f"Ação desconhecida: {payload.action}")

        # Registra o comando na tabela commands
        from app.models.command import Command
        cmd = Command(
            device_id=device_id,
            issued_by=user_id,
            command_type=cmd_type,
            value=payload.value,
            status=CommandStatus.EXECUTED,
            executed_at=now,
        )
        self._db.add(cmd)
        await self._db.flush()

        await self._audit.log(
            action="device_control", user_id=user_id, resource=str(device_id),
            metadata={"action": payload.action, "value": payload.value},
        )

        # Marca override manual (RN04) — suspende automações por 30 min
        from app.mqtt.handlers import mark_manual_override
        mark_manual_override(str(device_id))

        # Publica comando via MQTT (B10)
        from app.mqtt.client import mqtt_client
        mqtt_client.publish_command(str(device_id), payload.action, payload.value)

        return DeviceControlResponse(
            status="success", device_id=device_id,
            action=payload.action, value=payload.value, timestamp=now,
        )

    @staticmethod
    def _to_response(device: Device) -> DeviceResponse:
        return DeviceResponse(
            id=device.id, room_id=device.room_id, device_type=device.device_type,
            model=device.model, serial_number=device.serial_number,
            status=device.status, is_active=device.is_active, power_on=device.power_on,
            setpoint_celsius=device.setpoint_celsius, mqtt_topic=device.mqtt_topic,
            notes=device.notes, last_seen_at=device.last_seen_at,
            created_at=device.created_at, updated_at=device.updated_at,
            links=DeviceResponse.build_links(device.id),
        )
