"""ORM — Tabela devices."""
from __future__ import annotations
import enum, uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class DeviceType(str, enum.Enum):
    AC = "ac"
    TEMPERATURE_SENSOR = "temperature_sensor"
    HUMIDITY_SENSOR = "humidity_sensor"
    PRESENCE_SENSOR = "presence_sensor"
    WINDOW_SENSOR = "window_sensor"


class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    device_type: Mapped[DeviceType] = mapped_column(
        Enum(DeviceType, name="device_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, name="device_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=DeviceStatus.OFFLINE,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    power_on: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    setpoint_celsius: Mapped[float | None] = mapped_column(Float, nullable=True)
    mqtt_topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    room = relationship("Room", back_populates="devices", lazy="select")

    def __repr__(self) -> str:
        return f"<Device id={self.id} type={self.device_type} status={self.status}>"
