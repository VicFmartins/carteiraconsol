import json
from contextlib import contextmanager

from app.core.exceptions import ETLInputError
from app.lambda_handlers import etl_handler
from app.schemas.etl import ETLFileResult, ETLRunResponse


class DummySettings:
    s3_bucket_name = "carteiraconsol-vi-001"

    def ensure_directories(self) -> None:
        return None


def build_result(source_file: str) -> ETLRunResponse:
    return ETLRunResponse(
        files_processed=1,
        total_rows_processed=6,
        total_rows_skipped=0,
        results=[
            ETLFileResult(
                source_file=source_file,
                raw_file="data/raw/sample_portfolio.csv",
                processed_file="data/processed/sample_portfolio.csv",
                rows_processed=6,
                rows_skipped=0,
                clients_created=1,
                accounts_created=1,
                assets_created=1,
                positions_upserted=6,
            )
        ],
    )


@contextmanager
def dummy_session_scope():
    yield object()


def test_lambda_handler_accepts_direct_s3_payload(monkeypatch) -> None:
    captured: dict = {}

    class FakeService:
        def __init__(self, session) -> None:
            captured["session"] = session

        def run_from_s3(self, *, s3_key=None, s3_prefix=None):
            captured["s3_key"] = s3_key
            captured["s3_prefix"] = s3_prefix
            return build_result(f"s3://bucket/{s3_key}")

    monkeypatch.setattr(etl_handler, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(etl_handler, "init_db", lambda: None)
    monkeypatch.setattr(etl_handler, "session_scope", dummy_session_scope)
    monkeypatch.setattr(etl_handler, "ETLService", FakeService)

    response = etl_handler.handler({"s3_key": "incoming/sample_portfolio.csv"}, None)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "success"
    assert body["files_processed"] == 1
    assert captured["s3_key"] == "incoming/sample_portfolio.csv"


def test_lambda_handler_accepts_s3_event_payload(monkeypatch) -> None:
    captured: dict = {}

    class FakeService:
        def __init__(self, session) -> None:
            captured["session"] = session

        def run_many_from_s3(self, s3_keys):
            captured["s3_keys"] = list(s3_keys)
            return build_result(f"s3://bucket/{captured['s3_keys'][0]}")

    monkeypatch.setattr(etl_handler, "get_settings", lambda: DummySettings())
    monkeypatch.setattr(etl_handler, "init_db", lambda: None)
    monkeypatch.setattr(etl_handler, "session_scope", dummy_session_scope)
    monkeypatch.setattr(etl_handler, "ETLService", FakeService)

    response = etl_handler.handler(
        {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "carteiraconsol-vi-001"},
                        "object": {"key": "incoming%2Fsample_portfolio.csv"},
                    }
                }
            ]
        },
        None,
    )

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "success"
    assert captured["s3_keys"] == ["incoming/sample_portfolio.csv"]


def test_lambda_handler_rejects_bucket_mismatch(monkeypatch) -> None:
    monkeypatch.setattr(etl_handler, "get_settings", lambda: DummySettings())

    response = etl_handler.handler(
        {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "different-bucket"},
                        "object": {"key": "incoming%2Fsample_portfolio.csv"},
                    }
                }
            ]
        },
        None,
    )

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"]["code"] == "etl_input_error"
