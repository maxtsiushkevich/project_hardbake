from enum import Enum

from pydantic import BaseModel, Field, field_validator
from typing import Dict


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

    @field_validator('isolation_forest')
    @classmethod
    def validate_isolation_forest(cls, v: Dict) -> Dict:
        if not isinstance(v, dict):
            raise ValueError("isolation_forest must be a dictionary")

        # Validate n_estimators
        n_estimators = v.get("n_estimators", 100)
        if not isinstance(n_estimators, int) or n_estimators <= 0:
            raise ValueError("n_estimators must be a positive integer")

        # Validate contamination
        contamination = v.get("contamination", 0.15)
        if not isinstance(contamination, (int, float)) or not (0 < contamination <= 0.5):
            raise ValueError("contamination must be a float between 0 and 0.5")

        # Validate n_jobs
        n_jobs = v.get("n_jobs", -1)
        if not isinstance(n_jobs, int) or n_jobs < -1 or n_jobs == 0:
            raise ValueError("n_jobs must be -1, positive integer, or None")

        return v

    @field_validator('one_class_svm')
    @classmethod
    def validate_one_class_svm(cls, v: Dict) -> Dict:
        if not isinstance(v, dict):
            raise ValueError("one_class_svm must be a dictionary")

        # Validate nu
        nu = v.get("nu", 0.05)
        if not isinstance(nu, (int, float)) or not (0 < nu <= 1):
            raise ValueError("nu must be a float between 0 and 1")

        # Validate kernel
        kernel = v.get("kernel", "rbf")
        if kernel not in ["linear", "poly", "rbf", "sigmoid", "precomputed"]:
            raise ValueError("kernel must be one of: linear, poly, rbf, sigmoid, precomputed")

        # Validate gamma
        gamma = v.get("gamma", "auto")
        if gamma != "auto" and gamma != "scale" and not isinstance(gamma, (int, float)):
            raise ValueError("gamma must be 'auto', 'scale' or a positive float")

        return v


class TrainingStatus(str, Enum):
    NOT_STARTED = "Not started"
    COLLECTING_DATA = "Collecting data"
    TRAINING = "Training"
    READY = "Ready"
    ERROR = "Error"
    STOPPED = "Stopped"


class ConsumerStatusEnum(str, Enum):
    NOT_RUNNING = "Not running"
    RUNNING = "Running"
    STOPPED = "Stopped"
    ERROR = "Error"

class ConsumerStatusResponse(BaseModel):
    status: ConsumerStatusEnum

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


class UploadStatus(str, Enum):
    UPLOADED = 'Uploaded'
    ERROR = 'Error'


class UploadStatusResponse(BaseModel):
    status: UploadStatus


class UpdateMinSamples(BaseModel):
    min_samples: int
    status: UpdateStatus
    error_info: str | None = None
