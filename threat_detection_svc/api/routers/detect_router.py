from fastapi import APIRouter, HTTPException, UploadFile, File
from starlette import status

from api.core.logger import logger
from api.exceptions.exceptions import RabbitMQError
from api.schemas.detect import StartStopResponse, DetectionStatusResponse, DetectionStatusEnum, BatchSizeResponse, \
    UploadStatusResponse, UploadStatus
from api.services.data_processor import DataProcessor
from api.services.detection_service import DetectionService
from api.utils.rabbitmq import RabbitMQClient

from pathlib import Path
import os

router = APIRouter(prefix="/detect", tags=["Detection management"])

model_storage = DetectionService()
processor = DataProcessor(RabbitMQClient(), model_storage)

MODELS_DIR = "models"
MODEL_FILENAME = "trained_models.joblib"
ALLOWED_EXTENSIONS = {".joblib", ".pkl"}

Path(MODELS_DIR).mkdir(exist_ok=True)


@router.post("/start",
             response_model=StartStopResponse,
             responses={
                 200: {"description": "OK"},
                 500: {"description": "Internal Server Error"},
                 503: {"description": "RabbitMQ is not available"},
             }
             )
async def start_detect():
    logger.info("Received request to start detection")
    try:
        await processor.start()
        logger.info("Detection process started successfully")
        return StartStopResponse(status=DetectionStatusEnum.RUNNING)
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
async def stop_detect():
    logger.info("Received request to stop detection")
    try:
        await processor.stop()
        logger.info("Detection process stopped successfully")
        return StartStopResponse(status=DetectionStatusEnum.STOPPED)
    except Exception as e:
        logger.exception(f"Failed to stop consumer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop consumer: {str(e)}"
        )


@router.post(
    "/upload_models/",
    responses={
        200: {"description": "Models uploaded successfully"},
        400: {"description": "Invalid file format"},
        500: {"description": "Server error while uploading file"},
    },
    response_model=UploadStatusResponse
)
async def upload_models(
        file: UploadFile = File(..., description="Model file for download")
):
    logger.info(f"Uploading model file: {file.filename}")
    save_path = Path(MODELS_DIR) / MODEL_FILENAME
    try:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Rejected file due to invalid extension: {file_ext}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        with open(save_path, "wb") as buffer:
            buffer.write(await file.read())

        logger.info(f"Model saved to {save_path}, loading model")
        model_storage.load_models(str(save_path))
        logger.info("Model loaded successfully")

        return UploadStatusResponse(status=UploadStatus.UPLOADED)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error while uploading model: {e}", exc_info=True)
        if save_path.exists():
            try:
                os.remove(save_path)
                logger.info(f"Corrupted model file removed: {save_path}")
            except Exception as remove_err:
                logger.warning(f"Failed to delete corrupted model file: {remove_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading file: {str(e)}"
        )


@router.get("/status", response_model=DetectionStatusResponse)
async def get_detection_status():
    detection_status = processor.get_status()
    logger.info(f"Detection status requested, returning: {detection_status}")
    return DetectionStatusResponse(status=detection_status)


@router.patch("/set_batch_size",
              response_model=BatchSizeResponse,
              responses={
                  200: {"description": "OK"},
                  400: {"description": "Incorrect batch size"},
              }
              )
async def set_batch_size(size: int):
    try:
        await model_storage.set_batch_size(size)
        logger.info(f"Batch size set to: {size}")
        return BatchSizeResponse(size=size)
    except ValueError as e:
        logger.warning(f"Invalid batch size: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/get_batch_size",
            response_model=BatchSizeResponse,
            responses={
                200: {"description": "OK"},
                500: {"description": "Internal Server Error"},
            }
            )
async def get_batch_size():
    try:
        result = await model_storage.get_batch_size()
        logger.info(f"Current batch size: {result}")
        return BatchSizeResponse(size=result)
    except Exception as e:
        logger.exception(f"Failed to retrieve batch size: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
