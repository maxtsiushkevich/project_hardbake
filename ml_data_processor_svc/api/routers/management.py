from fastapi import APIRouter, HTTPException
from starlette import status

from api.core.logger import logger
from api.schemas.management import StartStopResponse, ConsumerStatusResponse
from api.services.consumer_manager import ConsumerManager
from api.services.stream_processor import StreamProcessor

router = APIRouter(prefix="/management", tags=["Management"])

proxy_packet_processor = StreamProcessor()
consumer_manager = ConsumerManager(proxy_packet_processor)


@router.post("/start",
             response_model=StartStopResponse,
             responses={
                 200: {"description": "OK"},
                 503: {"description": "RabbitMQ not available"},
             }
             )
async def start_consumer_endpoint():
    logger.info(f"Received request to start consumer")
    try:
        response = await consumer_manager.start()
        logger.info(f"Consumer started with status: {response['status']}")
        return StartStopResponse(status=response["status"])
    except Exception as e:
        logger.error(f"Failed to start consumer: {e}")
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
        logger.info(f"Consumer stopped with status: {response['status']}")
        return StartStopResponse(status=response["status"])
    except Exception as e:
        logger.error(f"Failed to stop consumer: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to stop consumer: {str(e)}"
        )


@router.get("/status", response_model=ConsumerStatusResponse)
async def get_consumer_status_endpoint():
    logger.debug("Received request for consumer status")
    status_data = consumer_manager.get_status()
    logger.debug(f"Consumer status: {status_data}")
    return ConsumerStatusResponse(status=status_data)
