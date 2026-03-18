from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import APIResponse
from app.schemas.etl import UploadResponse
from app.services.etl_service import ETLService


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=APIResponse[UploadResponse])
async def upload_portfolio_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> APIResponse[UploadResponse]:
    service = ETLService(db)
    temp_path = service.save_uploaded_file(file.filename or "", file.file)
    try:
        result = service.process_uploaded_file(temp_path, original_filename=file.filename)
        return APIResponse(data=result)
    finally:
        temp_path.unlink(missing_ok=True)
        logger.info("Removed temporary uploaded file %s", temp_path)
