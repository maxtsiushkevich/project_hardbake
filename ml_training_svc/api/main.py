from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.logger import LOGGING_CONFIG
from api.monitoring.prometheus import metrics, instrumentator
from api.routers.train_router import router as train_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(lifespan=lifespan, title='Project Hardbake. ML Training Service')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator.instrument(app, metric_namespace="ml_training_svc").expose(app)

app.mount("/metrics", metrics)

app.include_router(train_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8004, log_config=LOGGING_CONFIG)
