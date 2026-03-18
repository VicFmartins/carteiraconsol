from __future__ import annotations

import json
import logging
from urllib.parse import unquote_plus

from app.core.config import get_settings
from app.core.exceptions import ApplicationError, ETLInputError
from app.db.session import init_db, session_scope
from app.services.etl_service import ETLService


logger = logging.getLogger(__name__)


def _lambda_response(status_code: int, payload: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload, default=str),
    }


def _load_event_payload(event: dict | str | None) -> dict:
    if event is None:
        return {}
    if isinstance(event, str):
        loaded = json.loads(event)
        if not isinstance(loaded, dict):
            raise ETLInputError("Lambda payload must be a JSON object.")
        return loaded
    if not isinstance(event, dict):
        raise ETLInputError("Unsupported Lambda payload type. Expected a JSON object.")

    body = event.get("body")
    if isinstance(body, str) and body.strip():
        loaded = json.loads(body)
        if not isinstance(loaded, dict):
            raise ETLInputError("Lambda body must be a JSON object.")
        merged = dict(event)
        merged.pop("body", None)
        merged.update(loaded)
        return merged
    return event


def _extract_s3_keys_from_event(event: dict) -> list[str]:
    records = event.get("Records")
    if not isinstance(records, list):
        return []

    keys: list[str] = []
    settings = get_settings()
    for record in records:
        if not isinstance(record, dict):
            continue
        s3_data = record.get("s3") or {}
        bucket_data = s3_data.get("bucket") or {}
        object_data = s3_data.get("object") or {}

        bucket_name = bucket_data.get("name")
        object_key = object_data.get("key")
        if not object_key:
            continue

        decoded_key = unquote_plus(str(object_key))
        if bucket_name and settings.s3_bucket_name and bucket_name != settings.s3_bucket_name:
            raise ETLInputError(
                f"S3 event bucket '{bucket_name}' does not match configured S3_BUCKET_NAME '{settings.s3_bucket_name}'."
            )
        keys.append(decoded_key)
    return keys


def _resolve_invocation(event: dict | str | None) -> tuple[str, dict]:
    payload = _load_event_payload(event)

    s3_keys = _extract_s3_keys_from_event(payload)
    if s3_keys:
        logger.info("Resolved Lambda invocation from S3 event with %s record(s).", len(s3_keys))
        return "s3_event", {"s3_keys": s3_keys}

    if payload.get("s3_key"):
        logger.info("Resolved Lambda invocation from direct S3 payload.")
        return "direct_s3", {"s3_key": str(payload["s3_key"]).strip()}

    if payload.get("s3_prefix"):
        logger.info("Resolved Lambda invocation from direct S3 prefix payload.")
        return "direct_s3", {"s3_prefix": str(payload["s3_prefix"]).strip()}

    if payload.get("source_path"):
        logger.info("Resolved Lambda invocation from direct local payload.")
        return "direct_local", {"source_path": str(payload["source_path"]).strip()}

    raise ETLInputError(
        "Unsupported Lambda payload. Provide 's3_key', 's3_prefix', 'source_path', or an S3 event with Records[]."
    )


def handler(event: dict | str | None, context: object | None) -> dict:
    del context

    try:
        settings = get_settings()
        invocation_type, invocation_payload = _resolve_invocation(event)

        settings.ensure_directories()
        init_db()

        with session_scope() as session:
            service = ETLService(session)
            if invocation_type == "s3_event":
                result = service.run_many_from_s3(invocation_payload["s3_keys"])
            elif invocation_type == "direct_s3":
                result = service.run_from_s3(
                    s3_key=invocation_payload.get("s3_key"),
                    s3_prefix=invocation_payload.get("s3_prefix"),
                )
            else:
                result = service.run(source_path=invocation_payload.get("source_path"))

        logger.info(
            "Lambda ETL invocation completed successfully: files_processed=%s total_rows_processed=%s",
            result.files_processed,
            result.total_rows_processed,
        )
        return _lambda_response(200, result.model_dump(mode="json"))
    except ApplicationError as exc:
        logger.exception("Lambda ETL invocation failed with an application error.")
        return _lambda_response(
            400,
            {"status": "error", "error": {"code": exc.error_code, "message": exc.message}},
        )
    except json.JSONDecodeError as exc:
        logger.exception("Lambda ETL invocation received invalid JSON.")
        return _lambda_response(
            400,
            {
                "status": "error",
                "error": {
                    "code": "invalid_json",
                    "message": f"Unable to parse Lambda payload as JSON: {exc.msg}",
                },
            },
        )
    except Exception as exc:  # pragma: no cover - defensive runtime path
        logger.exception("Lambda ETL invocation failed unexpectedly.")
        return _lambda_response(
            500,
            {
                "status": "error",
                "error": {"code": "internal_server_error", "message": str(exc)},
            },
        )
