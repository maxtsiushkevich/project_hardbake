from fastapi import APIRouter, HTTPException
from starlette import status

from api.exceptions.exceptions import ModelUploadError
from api.schemas.detect import StartStopResponse, DetectionStatusResponse, DetectionStatusEnum
from api.services.data_processor import DataProcessor
from api.services.model_storage import ModelStorage
from api.utils.rabbitmq import RabbitMQClient

router = APIRouter(prefix="/detect", tags=["Detection management"])

model_storage = ModelStorage()
processor = DataProcessor(RabbitMQClient(), model_storage)


@router.post("/start", response_model=StartStopResponse)
async def start_detect():
    try:
        await processor.start()
        return StartStopResponse(status=DetectionStatusEnum.RUNNING)
    except RabbitMQClient as e:
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


@router.post("/upload_models")
async def load_models(path: str = "models.joblib"):
    try:
        model_storage.load_models(path)
        return {"status": "loaded", "path": path}
    except ModelUploadError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status", response_model=DetectionStatusResponse)
async def get_detection_status():
    detection_status = processor.get_status()
    return DetectionStatusResponse(status=detection_status)


@router.post("/set_batch_size")
async def set_batch_size(size: int):
    try:
        model_storage.set_batch_size(size)
        return {"status": "success", "batch_size": size}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set batch size: {str(e)}"
        )
