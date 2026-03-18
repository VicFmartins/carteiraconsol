from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import ORMModel


class IngestionReportRead(ORMModel):
    id: int
    filename: str
    source_file: str
    source_type: str
    detected_type: str
    raw_file: str | None = None
    processed_file: str | None = None
    parser_name: str | None = None
    detection_confidence: float | None = None
    review_required: bool
    review_reasons: list[str] = Field(default_factory=list)
    detected_columns: list[str] = Field(default_factory=list)
    applied_mappings: list[dict[str, object]] = Field(default_factory=list)
    structure_detection: dict[str, object] = Field(default_factory=dict)
    rows_processed: int = Field(ge=0)
    rows_skipped: int = Field(ge=0)
    status: str
    message: str
    created_at: datetime
    processed_at: datetime | None = None
