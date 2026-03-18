from __future__ import annotations

import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO
from typing import Iterable
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ETLInputError, ResourceNotFoundError
from app.db.session import session_scope
from app.etl.extract.file_reader import discover_input_files
from app.etl.pipeline import PortfolioETLPipeline
from app.schemas.etl import ETLFileResult, ETLRunResponse, UploadResponse


logger = logging.getLogger(__name__)


class ETLService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.pipeline = PortfolioETLPipeline(db)

    def run(self, source_path: str | None = None, *, source_type: str = "local") -> ETLRunResponse:
        files = self._resolve_local_files(source_path)
        summaries = [self.pipeline.run(file_path, source_type=source_type) for file_path in files]
        return self._build_response(summaries)

    def run_from_s3(self, *, s3_key: str | None = None, s3_prefix: str | None = None) -> ETLRunResponse:
        summary = self.pipeline.run(source_type="s3", s3_key=s3_key, s3_prefix=s3_prefix)
        return self._build_response([summary])

    def run_many_from_s3(self, s3_keys: Iterable[str]) -> ETLRunResponse:
        summaries = [self.pipeline.run(source_type="s3", s3_key=s3_key) for s3_key in s3_keys]
        return self._build_response(summaries)

    def save_uploaded_file(self, filename: str, file_stream: BinaryIO) -> Path:
        cleaned_name = Path(filename or "").name
        if not cleaned_name:
            raise ETLInputError("Uploaded file must include a valid filename.")

        suffix = Path(cleaned_name).suffix.lower()
        if suffix not in self.settings.supported_extensions:
            supported = ", ".join(self.settings.supported_extensions)
            raise ETLInputError(f"Unsupported uploaded file type '{suffix}'. Supported types: {supported}.")

        upload_dir = self.settings.raw_data_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        destination = upload_dir / f"upload_{uuid4().hex}{suffix}"
        file_stream.seek(0)
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file_stream, buffer)

        logger.info("Saved uploaded file %s to temporary work path %s", cleaned_name, destination)
        return destination

    def process_uploaded_file(self, file_path: str | Path, *, original_filename: str | None = None) -> UploadResponse:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise ResourceNotFoundError(f"Uploaded working file not found: {path}")

        suffix = path.suffix.lower()
        if suffix not in self.settings.supported_extensions:
            supported = ", ".join(self.settings.supported_extensions)
            raise ETLInputError(f"Unsupported uploaded file type '{suffix}'. Supported types: {supported}.")

        summary = self.pipeline.run(path, source_type="local")
        filename = original_filename or path.name
        return UploadResponse(
            filename=filename,
            detected_type=self._detect_uploaded_type(path),
            rows_processed=summary.rows_processed,
            rows_skipped=summary.rows_skipped,
            message=f"Arquivo {filename} processado com sucesso.",
            processed_at=datetime.now(UTC).isoformat(),
            raw_file=str(summary.raw_file),
            processed_file=str(summary.processed_file),
            detection_confidence=summary.detection_confidence,
            review_required=summary.review_required,
            review_reasons=list(summary.review_reasons),
        )

    @classmethod
    def process_uploaded_stream(cls, filename: str, file_stream: BinaryIO) -> UploadResponse:
        with session_scope() as db:
            service = cls(db)
            temp_path = service.save_uploaded_file(filename, file_stream)
            try:
                return service.process_uploaded_file(temp_path, original_filename=filename)
            finally:
                temp_path.unlink(missing_ok=True)
                logger.info("Removed temporary uploaded file %s", temp_path)

    def _build_response(self, summaries) -> ETLRunResponse:
        results = [
            ETLFileResult(
                source_file=summary.source_file,
                raw_file=str(summary.raw_file),
                processed_file=str(summary.processed_file),
                rows_processed=summary.rows_processed,
                rows_skipped=summary.rows_skipped,
                clients_created=summary.clients_created,
                accounts_created=summary.accounts_created,
                assets_created=summary.assets_created,
                positions_upserted=summary.positions_upserted,
                detection_confidence=summary.detection_confidence,
                review_required=summary.review_required,
                review_reasons=list(summary.review_reasons),
            )
            for summary in summaries
        ]

        return ETLRunResponse(
            files_processed=len(results),
            total_rows_processed=sum(item.rows_processed for item in results),
            total_rows_skipped=sum(item.rows_skipped for item in results),
            results=results,
        )

    def _resolve_local_files(self, source_path: str | None) -> list[Path]:
        if source_path:
            path = Path(source_path).expanduser().resolve()
            if not path.exists():
                raise ResourceNotFoundError(f"Input file not found: {path}")
            if path.is_dir():
                return [path]
            return [path]

        raw_files = discover_input_files(self.settings.raw_data_dir)
        if raw_files:
            return raw_files

        sample_files = discover_input_files(self.settings.samples_dir)
        if sample_files:
            return sample_files

        real_input_files = discover_input_files(self.settings.real_inputs_dir)
        if real_input_files:
            return [self.settings.real_inputs_dir]

        raise ResourceNotFoundError("No supported input files were found in data/raw, data/samples, or data/real_inputs.")

    @staticmethod
    def _detect_uploaded_type(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return "csv"
        if suffix in {".xlsx", ".xls"}:
            return "excel"
        if suffix == ".json":
            return "json"
        return suffix.lstrip(".") or "unknown"
