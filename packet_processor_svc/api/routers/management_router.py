from fastapi import APIRouter, HTTPException
from starlette import status
from starlette.responses import JSONResponse

from api.core.logger import logger
from api.schemas.management import StartStopResponse, ConsumerStatusResponse, ConsumerStatusEnum
from api.services.consumer_manager import ConsumerManager
from api.services.proxy_packet_processor import ProxyPacketProcessor

router = APIRouter(prefix="/management", tags=["Management"])

proxy_packet_processor = ProxyPacketProcessor()
consumer_manager = ConsumerManager(proxy_packet_processor)


@router.post("/start",
             response_model=StartStopResponse,
             responses={
                 200: {"description": "OK"},
                 503: {"description": "RabbitMQ not available"},
             }
             )
async def start_consumer_endpoint(udp_timeout: int = 10):
    logger.info(f"Received request to start consumer with udp_timeout={udp_timeout}")
    try:
        response = await consumer_manager.start(udp_timeout=udp_timeout)
        if response["status"] == ConsumerStatusEnum.RUNNING:
            logger.info("Consumer started successfully")
            return JSONResponse(content=StartStopResponse(status=response["status"]).model_dump(),
                                status_code=status.HTTP_200_OK)
        if response["status"] == ConsumerStatusEnum.NOT_RUNNING:
            logger.warning("Consumer could not start, RabbitMQ not available")
            return JSONResponse(content=StartStopResponse(status=response["status"]).model_dump(),
                                status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Failed to start consumer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to start consumer: {str(e)}"
        )


@router.post("/stop",
             response_model=StartStopResponse,
             responses={
                 200: {"description": "OK"},
                 503: {"description": "RabbitMQ not available"},
             }
             )
async def stop_consumer_endpoint():
    logger.info("Received request to stop consumer")
    try:
        response = await consumer_manager.stop()
        logger.info("Consumer stopped successfully")
        return StartStopResponse(status=response["status"])
    except Exception as e:
        logger.error(f"Failed to stop consumer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to stop consumer: {str(e)}"
        )


@router.get("/status", response_model=ConsumerStatusResponse)
async def get_consumer_status_endpoint():
    status_data = consumer_manager.get_status()
    logger.debug(f"Consumer status queried: {status_data}")
    return ConsumerStatusResponse(status=status_data)
