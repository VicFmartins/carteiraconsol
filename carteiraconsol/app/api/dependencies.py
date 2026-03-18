from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import Query

from app.schemas.common import PaginationParams


def pagination_params(
    offset: Annotated[int, Query(ge=0, description="Zero-based record offset")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum records to return")] = 50,
) -> PaginationParams:
    return PaginationParams(offset=offset, limit=limit)


def optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def optional_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)
