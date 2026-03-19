from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import optional_string
from app.db.session import get_db
from app.services.portfolio_report_service import PortfolioReportService


router = APIRouter(prefix="/reports")


@router.get("/portfolio/pdf", response_class=StreamingResponse)
def download_portfolio_pdf_report(
    db: Session = Depends(get_db),
    client_name: Annotated[str | None, Query(description="Optional exact client name filter")] = None,
    asset_class: Annotated[str | None, Query(description="Optional asset class filter")] = None,
    reference_date: Annotated[date | None, Query(description="Optional reference date filter (YYYY-MM-DD)")] = None,
) -> StreamingResponse:
    resolved_client_name = optional_string(client_name)
    resolved_asset_class = optional_string(asset_class)

    pdf_bytes = PortfolioReportService(db).generate_pdf(
        client_name=resolved_client_name,
        asset_class=resolved_asset_class,
        reference_date=reference_date,
    )
    filename = "carteiraconsol_executive_portfolio_report.pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    return StreamingResponse(BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
