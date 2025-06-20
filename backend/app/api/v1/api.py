from fastapi import APIRouter
from .endpoints import auth, financial_components, scenarios, partnerships

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(financial_components.router, prefix="/financial-components", tags=["financial-components"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(partnerships.router, prefix="/partnerships", tags=["partnerships"]) 