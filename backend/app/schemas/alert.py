"""Schemas Pydantic — Alertas."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.alert import AlertType, AlertSeverity
from app.schemas.base import HateoasLink


class AlertCreate(BaseModel):
    device_id: uuid.UUID
    alert_type: AlertType
    severity: AlertSeverity
    message: Optional[str] = None


class AlertResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    alert_type: AlertType
    severity: AlertSeverity
    message: Optional[str] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
    links: List[HateoasLink] = Field(default_factory=list)

    model_config = {"from_attributes": True}

    @staticmethod
    def build_links(alert_id: uuid.UUID) -> List[HateoasLink]:
        base = f"/api/v1/alerts/{alert_id}"
        return [
            HateoasLink(rel="self", href=base),
            HateoasLink(rel="acknowledge", href=f"{base}/acknowledge", method="POST"),
        ]
