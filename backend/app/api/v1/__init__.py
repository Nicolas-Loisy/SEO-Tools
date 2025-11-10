"""API v1 router."""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, projects, crawl, pages, analysis, usage, content

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(crawl.router, prefix="/crawl", tags=["Crawl"])
api_router.include_router(pages.router, prefix="/pages", tags=["Pages"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(usage.router, prefix="/usage", tags=["Usage & Quotas"])
api_router.include_router(content.router, prefix="/content", tags=["Content Generation"])
