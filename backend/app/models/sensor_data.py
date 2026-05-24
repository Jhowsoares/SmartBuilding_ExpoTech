"""ORM — Tabela sensor_data."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    tick: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                   default=lambda: datetime.now(timezone.utc), server_default="now()")

    __table_args__ = (
        Index("idx_sd_sensor_ts", "sensor_id", "timestamp"),
        Index("idx_sd_tipo_ts", "tipo", "timestamp"),
    )

    def __repr__(self) -> str:
        return f"<SensorData id={self.id} sensor={self.sensor_id} tipo={self.tipo} valor={self.valor}>"
