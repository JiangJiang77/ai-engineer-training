"""健康检查 API"""
from fastapi import APIRouter, HTTPException

from smart_customer_service_extend.api.models import HealthResponse
from smart_customer_service_extend.server import api_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查接口"""
    health_status = await api_service.check_health()
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    return health_status
