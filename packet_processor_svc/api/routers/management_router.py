from fastapi import APIRouter, HTTPException
from starlette import status

from api.schemas.management import StartStopResponse, ConsumerStatusResponse
from api.services.management_service import ConsumerManager
from api.services.proxy_packet_processor import ProxyPacketProcessor

router = APIRouter(prefix="/management", tags=["Management"])

proxy_packet_processor = ProxyPacketProcessor()
consumer_manager = ConsumerManager(proxy_packet_processor)


@router.post("/start", response_model=StartStopResponse)
async def start_consumer_endpoint():
    try:
        response = await consumer_manager.start()
        return StartStopResponse(status=response["status"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start consumer: {str(e)}"
        )


@router.post("/stop", response_model=StartStopResponse)
async def stop_consumer_endpoint():
    try:
        response = await consumer_manager.stop()
        return StartStopResponse(status=response["status"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop consumer: {str(e)}"
        )


@router.get("/status", response_model=ConsumerStatusResponse)
async def get_consumer_status_endpoint():
    status_data = consumer_manager.get_status()
    return ConsumerStatusResponse(status=status_data)
