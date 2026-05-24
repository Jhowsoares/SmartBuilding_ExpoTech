"""Importa todos os modelos ORM para registro no Base.metadata."""
from app.models.sensor_data import SensorData
from app.models.user import User, UserRole
from app.models.room import Room
from app.models.device import Device, DeviceType, DeviceStatus
from app.models.command import Command, CommandType, CommandStatus
from app.models.prediction import Prediction
from app.models.alert import Alert, AlertType, AlertSeverity
from app.models.audit_log import AuditLog

__all__ = [
    "SensorData", "User", "UserRole", "Room",
    "Device", "DeviceType", "DeviceStatus",
    "Command", "CommandType", "CommandStatus",
    "Prediction",
    "Alert", "AlertType", "AlertSeverity",
    "AuditLog",
]
