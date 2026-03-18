from __future__ import annotations

import io
from datetime import date
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.account import Account
from app.models.asset_master import AssetMaster
from app.models.client import Client
from app.models.position_history import PositionHistory
from app.schemas.etl import UploadResponse
from app.services.etl_service import ETLService


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    database_path = tmp_path / "api_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("AUTO_CREATE_TABLES", "false")

    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    session: Session = TestingSessionLocal()
    try:
        client_1 = Client(name="Ana Costa", risk_profile="arrojado")
        client_2 = Client(name="Maria Oliveira", risk_profile="moderado")
        session.add_all([client_1, client_2])
        session.flush()

        account_1 = Account(client_id=client_1.id, broker="XP")
        account_2 = Account(client_id=client_2.id, broker="BTG")
        session.add_all([account_1, account_2])
        session.flush()

        asset_1 = AssetMaster(
            ticker="PETR4",
            original_name="PETR4",
            normalized_name="PETR4",
            asset_class="equities",
            cnpj="00.000.000/0001-00",
            maturity_date=None,
        )
        asset_2 = AssetMaster(
            ticker="BTC",
            original_name="Bitcoin",
            normalized_name="BITCOIN",
            asset_class="crypto",
            cnpj=None,
            maturity_date=None,
        )
        session.add_all([asset_1, asset_2])
        session.flush()

        session.add_all(
            [
                PositionHistory(
                    account_id=account_1.id,
                    asset_id=asset_1.id,
                    quantity=Decimal("10"),
                    avg_price=Decimal("30"),
                    total_value=Decimal("300"),
                    reference_date=date(2026, 3, 15),
                ),
                PositionHistory(
                    account_id=account_2.id,
                    asset_id=asset_2.id,
                    quantity=Decimal("0.1"),
                    avg_price=Decimal("500000"),
                    total_value=Decimal("50000"),
                    reference_date=date(2026, 3, 16),
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    engine.dispose()


def test_clients_endpoint_supports_pagination_and_filtering(api_client: TestClient) -> None:
    response = api_client.get("/clients", params={"risk_profile": "moderado", "limit": 1, "offset": 0})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["pagination"] == {
        "total": 1,
        "offset": 0,
        "limit": 1,
        "count": 1,
        "has_more": False,
    }
    assert payload["data"][0]["name"] == "Maria Oliveira"


def test_assets_endpoint_supports_search(api_client: TestClient) -> None:
    response = api_client.get("/assets", params={"search": "bit"})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 1
    assert payload["data"][0]["asset_class"] == "crypto"


def test_positions_endpoint_returns_validation_errors_in_standard_format(api_client: TestClient) -> None:
    response = api_client.get("/positions", params={"limit": 0})

    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error_code"] == "request_validation_error"
    assert payload["errors"][0]["field"] == "limit"


def test_upload_endpoint_processes_a_supported_file(api_client: TestClient) -> None:
    csv_content = "\n".join(
        [
            "cliente,perfil,corretora,ativo,ticker,quantidade,preco medio,valor total,data referencia",
            "Carlos Lima,moderado,XP,Tesouro Selic 2029,SELIC29,2,10100.50,20201.00,2026-03-17",
        ]
    ).encode("utf-8")

    response = api_client.post(
        "/upload",
        files={"file": ("carteira.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["filename"] == "carteira.csv"
    assert payload["data"]["detected_type"] == "csv"
    assert payload["data"]["rows_processed"] == 1
    assert payload["data"]["processed_at"]
    datetime.fromisoformat(payload["data"]["processed_at"])

    positions_response = api_client.get("/positions")
    assert positions_response.status_code == 200
    assert positions_response.json()["pagination"]["total"] == 3

    Path(payload["data"]["raw_file"]).unlink(missing_ok=True)
    Path(payload["data"]["processed_file"]).unlink(missing_ok=True)


def test_upload_endpoint_rejects_unsupported_extension(api_client: TestClient) -> None:
    response = api_client.post(
        "/upload",
        files={"file": ("notas.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error_code"] == "etl_input_error"


def test_upload_endpoint_materializes_file_before_executor(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_process_uploaded_stream(filename: str, file_stream: io.BytesIO) -> UploadResponse:
        captured["filename"] = filename
        captured["stream_type"] = type(file_stream)
        captured["content"] = file_stream.read()
        return UploadResponse(
            filename=filename,
            detected_type="csv",
            rows_processed=1,
            rows_skipped=0,
            message="ok",
            processed_at=datetime.now().isoformat(),
            raw_file="data/raw/upload.csv",
            processed_file="data/processed/normalized.csv",
        )

    monkeypatch.setattr(ETLService, "process_uploaded_stream", fake_process_uploaded_stream)

    response = api_client.post(
        "/upload",
        files={"file": ("carteira.csv", b"coluna\nvalor\n", "text/csv")},
    )

    assert response.status_code == 200
    assert captured["filename"] == "carteira.csv"
    assert captured["stream_type"] is io.BytesIO
    assert captured["content"] == b"coluna\nvalor\n"
