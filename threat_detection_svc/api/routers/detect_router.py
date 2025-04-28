from fastapi import APIRouter, HTTPException, UploadFile, File
from starlette import status

from api.exceptions.exceptions import ModelUploadError, RabbitMQError
from api.schemas.detect import StartStopResponse, DetectionStatusResponse, DetectionStatusEnum, BatchSizeResponse, \
    UploadStatusResponse, UploadStatus
from api.services.data_processor import DataProcessor
from api.services.model_storage import ModelStorage
from api.utils.rabbitmq import RabbitMQClient

from pathlib import Path
import os

router = APIRouter(prefix="/detect", tags=["Detection management"])

model_storage = ModelStorage()
processor = DataProcessor(RabbitMQClient(), model_storage)

MODELS_DIR = "models"
MODEL_FILENAME = "trained_models.joblib"
ALLOWED_EXTENSIONS = {".joblib", ".pkl"}

Path(MODELS_DIR).mkdir(exist_ok=True)


@router.post("/start", response_model=StartStopResponse)
async def start_detect():
    try:
        await processor.start()
        return StartStopResponse(status=DetectionStatusEnum.RUNNING)
    except RabbitMQError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/stop", response_model=StartStopResponse)
async def stop_detect():
    try:
        await processor.stop()
        return StartStopResponse(status=DetectionStatusEnum.STOPPED)
    except Exception as e:
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
    save_path = Path(MODELS_DIR) / MODEL_FILENAME
    try:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        with open(save_path, "wb") as buffer:
            buffer.write(await file.read())

        model_storage.load_models(str(save_path))

        return UploadStatusResponse(status=UploadStatus.UPLOADED)

    except HTTPException:
        raise
    except Exception as e:
        if save_path.exists():
            try:
                os.remove(save_path)
            except:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading file: {str(e)}"
        )


@router.get("/status", response_model=DetectionStatusResponse)
async def get_detection_status():
    detection_status = processor.get_status()
    return DetectionStatusResponse(status=detection_status)


@router.patch("/set_batch_size", response_model=BatchSizeResponse)
async def set_batch_size(size: int):
    try:
        await model_storage.set_batch_size(size)
        return BatchSizeResponse(size=size)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/get_batch_size", response_model=BatchSizeResponse)
async def get_batch_size():
    try:
        result = await model_storage.get_batch_size()
        return BatchSizeResponse(size=result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
