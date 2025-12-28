from fastapi import APIRouter
from app.api.v1.endpoints import auth, document, plagiarism, report

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(document.router, prefix="/documents", tags=["Documents"])
api_router.include_router(plagiarism.router, prefix="/plagiarism", tags=["Plagiarism Check"])
api_router.include_router(report.router, prefix="/reports", tags=["Reports"])