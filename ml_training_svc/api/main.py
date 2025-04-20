from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from api.monitoring.prometheus import metrics, instrumentator
from api.routers.train_router import router as train_router
from api.utils.rabbitmq import RabbitMQClient

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    #shutdown


app = FastAPI(lifespan=lifespan, title='Project Hardbake. ML Training Service')

instrumentator.instrument(app, metric_namespace="ml_training_svc").expose(app)

app.mount("/metrics", metrics)

app.include_router(train_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8004)
