from enum import Enum

from pydantic import Field, BaseModel


class ModelHyperparameters(BaseModel):
    isolation_forest: dict = Field(
        default={
            "n_estimators": 100,
            "contamination": 0.15,
            "n_jobs": -1
        },
        description="Hyperparameters for Isolation Forest"
    )
    one_class_svm: dict = Field(
        default={
            "nu": 0.05,
            "kernel": "rbf",
            "gamma": "auto"
        },
        description="Hyperparameters for OneClassSVM"
    )


class TrainingStatus(str, Enum):
    NOT_STARTED = "Not started"
    COLLECTING_DATA = "Collecting data"
    TRAINING = "Training"
    READY = "Ready"
    ERROR = "Error"


class ModelSettings(BaseModel):
    hyperparameters: ModelHyperparameters
    min_samples_for_training: int
    current_samples: int
    training_status: TrainingStatus


class TrainingInfoResponse(BaseModel):
    training_status: TrainingStatus
    collected_samples: int
    min_samples_for_training: int


class Status(str, Enum):
    STARTED = 'Started'
    STOPPED = 'Stopped'
    UPDATED = 'Updated'
    SAVED = 'Saved'
    LOADED = 'Loaded'


class UpdateStatus(str, Enum):
    UPDATED = 'Updated'
    ERROR = 'Error'


class StatusResponse(BaseModel):
    status: Status


class UpdateHyperparametersResponse(BaseModel):
    status: UpdateStatus
    hyperparameters: ModelHyperparameters


class UpdateMinSamples(BaseModel):
    min_samples: int
    status: UpdateStatus
    error_info: str | None = None
