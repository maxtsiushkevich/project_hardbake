from enum import Enum

from pydantic import Field, BaseModel


class ModelHyperparameters(BaseModel):
    isolation_forest: dict = Field(
        default={
            "n_estimators": 1000,
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
    NOT_STARTED = "not_started"
    COLLECTING_DATA = "collecting_data"
    TRAINING = "training"
    READY = "ready"
    ERROR = "error"
