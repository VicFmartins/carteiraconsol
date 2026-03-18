from fastapi import APIRouter

from app.api.routes import accounts, assets, clients, etl, health, positions, upload


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(positions.router, prefix="/positions", tags=["positions"])
api_router.include_router(etl.router, prefix="/etl", tags=["etl"])
