"""Schemas Pydantic V2 do Smart Building."""
from app.schemas.base import HateoasLink, PaginationMeta, PaginatedResponse, ErrorResponse
from app.schemas.sensor import SensorTipo, SensorStatus, SensorDataIngest, SensorDataResponse, SensorLatestResponse, SensorResponse, SensorListResponse
from app.schemas.token import LoginRequest, TokenResponse, RefreshRequest

__all__ = [
    "HateoasLink", "PaginationMeta", "PaginatedResponse", "ErrorResponse",
    "SensorTipo", "SensorStatus", "SensorDataIngest", "SensorDataResponse",
    "SensorLatestResponse", "SensorResponse", "SensorListResponse",
    "LoginRequest", "TokenResponse", "RefreshRequest",
]
