from fastapi import APIRouter

from backend.app.services.content_service import ContentService

router = APIRouter(prefix="/content", tags=["Admin"])
content_service = ContentService()


