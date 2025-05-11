from fastapi import APIRouter, HTTPException
from starlette import status

from api.core.logger import logger
from api.exceptions.exceptions import RabbitMQError
from api.schemas.consumer import StartStopResponse, ConsumingsStatusResponse, ConsumingStatusEnum
from api.services.consumer_manager import ConsumerManager
from api.utils.rabbitmq import RabbitMQClient

router = APIRouter(prefix="/notification", tags=["Notifications"])

processor = ConsumerManager(RabbitMQClient())


@router.post("/start",
             response_model=StartStopResponse,
             responses={
                 200: {"description": "OK"},
                 500: {"description": "Internal Server Error"},
                 503: {"description": "RabbitMQ is not available"},
             }
             )
async def start_consuming():
    logger.info("Received request to start detection")
    try:
        await processor.start()
        logger.info("Detection process started successfully")
        return StartStopResponse(status=ConsumingStatusEnum.RUNNING)
    except RabbitMQError as e:
        logger.error(f"RabbitMQ error during start: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error while starting detection: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/stop", response_model=StartStopResponse,
             responses={
                 200: {"description": "OK"},
                 500: {"description": "Internal Server Error"},
             }
             )
async def stop_consuming():
    logger.info("Received request to stop detection")
    try:
        await processor.stop()
        logger.info("Detection process stopped successfully")
        return StartStopResponse(status=ConsumingStatusEnum.STOPPED)
    except Exception as e:
        logger.exception(f"Failed to stop consumer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop consumer: {str(e)}"
        )


@router.get("/status", response_model=ConsumingsStatusResponse)
async def get_consuming_status():
    detection_status = processor.get_status()
    logger.info(f"Detection status requested, returning: {detection_status}")
    return ConsumingsStatusResponse(status=detection_status)
