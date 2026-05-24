"""Repositórios de acesso ao banco."""
from app.repositories.sensor_repository import SensorRepository
from app.repositories.audit_repository import AuditRepository
__all__ = ["SensorRepository", "AuditRepository"]
