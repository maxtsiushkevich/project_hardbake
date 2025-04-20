import asyncio

from fastapi import APIRouter, HTTPException
from starlette import status

from api.exceptions.exceptions import NotEnoughTrainingRecords, ModelsNotReady
from api.schemas.ml import ModelHyperparameters, TrainingStatus
from api.services.ml_data_processor import MLDataProcessor
from api.services.model_storage import ModelStorage
from api.utils.rabbitmq import RabbitMQClient

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

model_storage = ModelStorage()
ml_processor = MLDataProcessor(RabbitMQClient(), model_storage)


@router.post("/start_consuming")
async def start_consuming():
    try:
        await ml_processor.start_consuming()
        model_storage.training_status = TrainingStatus.COLLECTING_DATA
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/stop_consuming")
async def stop_consuming():
    try:
        await ml_processor.stop_consuming()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/train")
async def train():
    try:
        asyncio.create_task(model_storage.train_models())  # запускаем в фоне
        return {"status": "started"}
    except NotEnoughTrainingRecords:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Not enough records for training'
        )


@router.get("/status")
async def get_status():
    return {
        "status": model_storage.training_status,
        "collected_samples": model_storage.get_len_of_training_data(),
        "min_samples_for_training": model_storage.min_samples_for_training
    }


@router.post("/update_hyperparameters")
async def update_hyperparameters(params: ModelHyperparameters):
    try:
        model_storage.hyperparameters = params
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/save_models")
async def save_models(path: str = "models.joblib"):
    try:
        model_storage.save_models(path)
        return {"status": "saved", "path": path}

    except ModelsNotReady as e:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT,
                            detail='Models not ready')
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/load_models")
async def load_models(path: str = "models.joblib"):
    try:
        model_storage.load_models(path)
        return {"status": "loaded", "path": path}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/set_min_samples")
async def set_min_samples(min_samples: int):
    if min_samples < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum samples should be at least 100"
        )
    model_storage.min_samples_for_training = min_samples
    return {"status": "updated", "min_samples": min_samples}


@router.get("/current_settings", response_model=dict)
async def get_current_settings():
    """Returns the current hyperparameter and training parameter settings"""
    try:
        return {
            "hyperparameters": model_storage.hyperparameters.model_dump(),
            "min_samples_for_training": model_storage.min_samples_for_training,
            "current_samples": model_storage.get_len_of_training_data(),
            "training_status": model_storage.training_status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current settings: {str(e)}"
        )
