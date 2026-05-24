"""Schemas base: HATEOAS, Paginação, Erros RFC 7807."""

from __future__ import annotations
from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class HateoasLink(BaseModel):
    rel: str
    href: str
    method: str = "GET"


class AuditFields(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaginationMeta(BaseModel):
    total: int
    page: int
    size: int
    total_pages: int
    links: List[HateoasLink] = Field(default_factory=list)


class PaginatedResponse(BaseModel, Generic[DataT]):
    data: List[DataT]
    meta: PaginationMeta


class ErrorResponse(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
