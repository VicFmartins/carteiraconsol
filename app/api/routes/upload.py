from __future__ import annotations

import asyncio
import io
import logging
from functools import partial

from fastapi import APIRouter, File, UploadFile

from app.schemas.common import APIResponse
from app.schemas.etl import UploadResponse
from app.services.etl_service import ETLService


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=APIResponse[UploadResponse])
async def upload_portfolio_file(
    file: UploadFile = File(...),
) -> APIResponse[UploadResponse]:
    file_bytes = await file.read()
    stream = io.BytesIO(file_bytes)
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        partial(ETLService.process_uploaded_stream, file.filename or "", stream),
    )
    logger.info("Completed uploaded file processing for %s", file.filename)
    return APIResponse(data=result)
