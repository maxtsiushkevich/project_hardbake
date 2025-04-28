import asyncio

from fastapi import APIRouter, HTTPException, UploadFile, File
from starlette import status

from api.exceptions.exceptions import NotEnoughTrainingRecords, ModelsNotReady, InvalidHyperparametersError, \
    UpdateMinSamplesException
from api.schemas.ml import ModelHyperparameters, TrainingStatus, ModelSettings, TrainingInfoResponse, \
    StatusResponse, Status, UpdateHyperparametersResponse, UpdateStatus, UpdateMinSamples, UploadStatusResponse, \
    UploadStatus
from api.services.ml_data_processor import MLDataProcessor
from api.services.model_storage import ModelStorage
from api.utils.rabbitmq import RabbitMQClient

from fastapi.responses import FileResponse
from pathlib import Path
import os

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

model_storage = ModelStorage()
ml_processor = MLDataProcessor(RabbitMQClient(), model_storage)

MODELS_DIR = "models"
MODEL_FILENAME = "trained_models.joblib"
ALLOWED_EXTENSIONS = {".joblib", ".pkl"}

Path(MODELS_DIR).mkdir(exist_ok=True)


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


@router.get(
    "/download_models/",
    responses={
        200: {
            "content": {"application/octet-stream": {}},
            "description": "Model file downloaded successfully",
        },
        204: {"description": "Models are not ready for download"},
        500: {"description": "Server error while downloading file"},
    }
)
async def download_models():
    try:
        file_path = Path(MODELS_DIR) / MODEL_FILENAME

        model_storage.save_models(str(file_path))

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Model file not found. Train models first"
            )

        if model_storage.training_status != TrainingStatus.READY:
            raise ModelsNotReady()

        return FileResponse(
            path=file_path,
            filename=MODEL_FILENAME,
            media_type="application/octet-stream"
        )

    except ModelsNotReady as e:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
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
