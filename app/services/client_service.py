from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.common import PaginationParams
from app.services.query_results import PagedResult, build_paged_result


class ClientService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_clients(
        self,
        *,
        pagination: PaginationParams,
        name: str | None = None,
        risk_profile: str | None = None,
    ) -> PagedResult[Client]:
        statement = select(Client)
        count_statement = select(func.count()).select_from(Client)

        if name:
            pattern = f"%{name.strip()}%"
            statement = statement.where(Client.name.ilike(pattern))
            count_statement = count_statement.where(Client.name.ilike(pattern))

        if risk_profile:
            normalized_risk_profile = risk_profile.strip().lower()
            statement = statement.where(Client.risk_profile == normalized_risk_profile)
            count_statement = count_statement.where(Client.risk_profile == normalized_risk_profile)

        items = list(
            self.db.scalars(
                statement.order_by(Client.name).offset(pagination.offset).limit(pagination.limit)
            ).all()
        )
        total = int(self.db.scalar(count_statement) or 0)
        return build_paged_result(items, total, pagination)
