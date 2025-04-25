import asyncio

from fastapi import APIRouter, HTTPException
from starlette import status

from api.exceptions.exceptions import NotEnoughTrainingRecords, ModelsNotReady, InvalidHyperparametersError, \
    UpdateMinSamplesException
from api.schemas.ml import ModelHyperparameters, TrainingStatus, ModelSettings, TrainingInfoResponse, \
    StatusResponse, Status, UpdateHyperparametersResponse, UpdateStatus, UpdateMinSamples
from api.services.ml_data_processor import MLDataProcessor
from api.services.model_storage import ModelStorage
from api.utils.rabbitmq import RabbitMQClient

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

model_storage = ModelStorage()
ml_processor = MLDataProcessor(RabbitMQClient(), model_storage)


@router.post("/start_consuming", response_model=StatusResponse)
async def start_consuming():
    try:
        await ml_processor.start_consuming()
        model_storage.training_status = TrainingStatus.COLLECTING_DATA
        return StatusResponse(status=Status.STARTED)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/stop_consuming", response_model=StatusResponse)
async def stop_consuming():
    try:
        await ml_processor.stop_consuming()
        return StatusResponse(status=Status.STOPPED)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/train", response_model=StatusResponse)
async def train():
    try:
        asyncio.create_task(model_storage.train_models())
        return StatusResponse(status=Status.STARTED)
    except NotEnoughTrainingRecords:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Not enough records for training'
        )


@router.get("/status", response_model=TrainingInfoResponse)
async def get_training_info():
    try:
        result = await model_storage.get_training_status()
        return TrainingInfoResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current settings: {str(e)}"
        )


@router.post("/update_hyperparameters", response_model=UpdateHyperparametersResponse)
async def update_hyperparameters(params: ModelHyperparameters):
    try:
        await model_storage.update_hyperparameters(params.model_dump())
        return UpdateHyperparametersResponse(status=UpdateStatus.UPDATED, hyperparameters=params)
    except InvalidHyperparametersError as e:
        return UpdateHyperparametersResponse(status=UpdateStatus.ERROR, hyperparameters=params)
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


@router.post("/set_min_samples", response_model=UpdateMinSamples)
async def set_min_samples_for_training(min_samples: int):
    try:
        await model_storage.update_min_samples(min_samples)
    except UpdateMinSamplesException as e:
        return UpdateMinSamples(min_samples=min_samples, status=UpdateStatus.ERROR, error_info=str(e))

    return UpdateMinSamples(min_samples=min_samples, status=UpdateStatus.UPDATED)


@router.get("/current_settings", response_model=ModelSettings)
async def get_current_settings():
    try:
        result = await model_storage.get_current_settings()
        return ModelSettings(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current settings: {str(e)}"
        )
