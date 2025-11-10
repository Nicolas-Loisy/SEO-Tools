"""API v1 router."""

from fastapi import APIRouter
from app.api.v1.endpoints import projects, crawl, pages

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(crawl.router, prefix="/crawl", tags=["Crawl"])
api_router.include_router(pages.router, prefix="/pages", tags=["Pages"])
