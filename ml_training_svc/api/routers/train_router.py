import asyncio

from fastapi import APIRouter, HTTPException, UploadFile, File
from starlette import status
from fastapi.responses import JSONResponse

from api.core.logger import logger
from api.exceptions.exceptions import NotEnoughTrainingRecords, ModelsNotReady, InvalidHyperparametersError, \
    UpdateMinSamplesException
from api.schemas.ml import ModelHyperparameters, TrainingStatus, ModelSettings, TrainingInfoResponse, \
    StatusResponse, Status, UpdateHyperparametersResponse, UpdateStatus, UpdateMinSamples, UploadStatusResponse, \
    UploadStatus
from api.services.ml_data_processor import MLDataProcessor
from api.services.model_storage import ModelStorage

from fastapi.responses import FileResponse
from pathlib import Path
import os

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

model_storage = ModelStorage()
ml_processor = MLDataProcessor(model_storage)

MODELS_DIR = "models"
MODEL_FILENAME = "trained_models.joblib"
ALLOWED_EXTENSIONS = {".joblib", ".pkl"}

Path(MODELS_DIR).mkdir(exist_ok=True)


@router.post("/start_consuming",
             response_model=StatusResponse,
             responses={
                 200: {"description": "OK"},
                 503: {"description": "RabbitMQ not available"},
             }
             )
async def start_consuming():
    logger.info("Received request to start consuming")
    try:
        await ml_processor.start_consuming()
        model_storage.training_status = TrainingStatus.COLLECTING_DATA
        logger.info("Started consuming messages for ML data collection")
        return StatusResponse(status=Status.STARTED)
    except Exception as e:
        logger.error(f"Failed to start consuming: {e}", exc_info=True)
        model_storage.training_status = TrainingStatus.ERROR
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@router.post("/stop_consuming",
             response_model=StatusResponse,
             responses={
                 200: {"description": "OK"},
                 503: {"description": "RabbitMQ not available"},
             }
             )
async def stop_consuming():
    logger.info("Received request to stop consuming")
    try:
        await ml_processor.stop_consuming()
        model_storage.training_status = TrainingStatus.STOPPED
        logger.info("Stopped consuming messages")
        return StatusResponse(status=Status.STOPPED)
    except Exception as e:
        logger.error(f"Failed to stop consuming: {e}", exc_info=True)
        model_storage.training_status = TrainingStatus.ERROR
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


@router.post("/train",
             response_model=StatusResponse,
             status_code=status.HTTP_202_ACCEPTED,
             responses={
                 202: {"description": "Training started"},
                 409: {"description": "Not enough records for training"},
             }
             )
async def train():
    logger.info("Received request to train models")
    try:
        asyncio.create_task(model_storage.train_models())
        logger.info("Started training models in background")
        return StatusResponse(status=Status.STARTED)
    except NotEnoughTrainingRecords:
        logger.warning("Not enough training records to start training")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Not enough records for training'
        )


@router.get("/status",
            response_model=TrainingInfoResponse,
            responses={
                200: {"description": "OK"},
                500: {"description": "Failed to get current settings"},
            }
            )
async def get_training_info():
    logger.info("Received request to get training status")
    try:
        result = await model_storage.get_training_status()
        logger.debug(f"Training status fetched: {result}")
        return TrainingInfoResponse(**result)
    except Exception as e:
        logger.error(f"Failed to get training status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current settings: {str(e)}"
        )


@router.post("/update_hyperparameters",
             response_model=UpdateHyperparametersResponse,
             responses={
                 200: {"description": "OK"},
                 400: {"description": "Incorrect hyperparameters",
                       "model": UpdateHyperparametersResponse},
                 500: {"description": "Internal server error"},
             }
             )
async def update_hyperparameters(params: ModelHyperparameters):
    logger.info(f"Received request to update_hyperparameters. New: {params}")
    try:
        await model_storage.update_hyperparameters(params.model_dump())
        logger.info("Hyperparameters updated successfully")
        return JSONResponse(
            content=UpdateHyperparametersResponse(status=UpdateStatus.UPDATED, hyperparameters=params).model_dump(),
            status_code=status.HTTP_200_OK)
    except InvalidHyperparametersError as e:
        logger.warning(f"Invalid hyperparameters: {e}")
        return JSONResponse(
            content=UpdateHyperparametersResponse(status=UpdateStatus.UPDATED, hyperparameters=params).model_dump(),
            status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Internal error updating hyperparameters: {e}", exc_info=True)
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
    logger.info("Received request to download models")
    try:
        file_path = Path(MODELS_DIR) / MODEL_FILENAME

        model_storage.save_models(str(file_path))

        if not file_path.exists():
            logger.warning("Model file does not exist")
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="Model file not found. Train models first"
            )

        if model_storage.training_status != TrainingStatus.READY:
            logger.warning("Models not ready for download")
            raise ModelsNotReady()

        logger.debug(f"Returning model file: {file_path}")
        return FileResponse(
            path=file_path,
            filename=MODEL_FILENAME,
            media_type="application/octet-stream"
        )

    except ModelsNotReady as e:
        logger.warning(f"ModelsNotReady error: {e}")
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}", exc_info=True)
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
    logger.info(f"Received file upload request: {file.filename}")

    save_path = Path(MODELS_DIR) / MODEL_FILENAME
    try:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Invalid file extension: {file_ext}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        with open(save_path, "wb") as buffer:
            buffer.write(await file.read())

        model_storage.load_models(str(save_path))
        logger.info("Model uploaded and loaded successfully")
        return UploadStatusResponse(status=UploadStatus.UPLOADED)

    except HTTPException:
        raise
    except Exception as e:
        if save_path.exists():
            try:
                os.remove(save_path)
                logger.info("Removed partially uploaded file after failure")
            except:
                logger.warning("Failed to remove broken file after exception")
        logger.error(f"Error during model upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading file: {str(e)}"
        )


@router.post("/set_min_samples",
             response_model=UpdateMinSamples,
             responses={
                 200: {"description": "OK"},
                 400: {"description": "Incorrect num of samples",
                       "model": UpdateMinSamples},
                 500: {"description": "Internal server error"},
             }
             )
async def set_min_samples_for_training(min_samples: int):
    logger.info(f"Received request to set min_samples: {min_samples}")
    try:
        await model_storage.update_min_samples(min_samples)
        logger.info("Minimum samples updated successfully")
    except UpdateMinSamplesException as e:
        logger.warning(f"Invalid min_samples value: {e}")
        return JSONResponse(
            content=UpdateMinSamples(min_samples=min_samples, status=UpdateStatus.ERROR,
                                     error_info=str(e)).model_dump(),
            status_code=status.HTTP_400_BAD_REQUEST)

    return UpdateMinSamples(min_samples=min_samples, status=UpdateStatus.UPDATED)


@router.get("/current_settings",
            response_model=ModelSettings,
            responses={
                200: {"description": "OK"},
                500: {"description": "Internal server error"},
            }
            )
async def get_current_settings():
    logger.info("Received request: get current model settings")
    try:
        result = await model_storage.get_current_settings()
        logger.debug(f"Current model settings: {result}")
        return ModelSettings(**result)
    except Exception as e:
        logger.error(f"Failed to get current settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current settings: {str(e)}"
        )
