"""ORM — Tabela alerts."""
from __future__ import annotations
import enum, uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AlertType(str, enum.Enum):
    HIGH_TEMPERATURE = "HIGH_TEMPERATURE"
    LOW_HUMIDITY = "LOW_HUMIDITY"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    WINDOW_OPEN = "WINDOW_OPEN"
    CONSUMPTION_LIMIT = "CONSUMPTION_LIMIT"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alert_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
