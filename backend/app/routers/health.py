from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    return JSONResponse({"status": "ok", "service": "FormPilot AI"})
