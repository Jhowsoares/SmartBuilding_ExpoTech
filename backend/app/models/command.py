"""ORM — Tabela commands."""
from __future__ import annotations
import enum, uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CommandType(str, enum.Enum):
    POWER_ON = "power_on"
    POWER_OFF = "power_off"
    SET_TEMPERATURE = "set_temperature"
    SET_MODE = "set_mode"


class CommandStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    EXECUTED = "executed"
    FAILED = "failed"


class Command(Base):
    __tablename__ = "commands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    issued_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    command_type: Mapped[CommandType] = mapped_column(
        Enum(CommandType, name="command_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CommandStatus] = mapped_column(
        Enum(CommandStatus, name="command_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=CommandStatus.PENDING,
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Command id={self.id} device={self.device_id} type={self.command_type} status={self.status}>"
