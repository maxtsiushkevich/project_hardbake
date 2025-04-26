from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from api.monitoring.prometheus import metrics, instrumentator
from api.routers.detect_router import router as detection_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(lifespan=lifespan, title='Project Hardbake. Threat Detection Service')

instrumentator.instrument(app, metric_namespace="threat_detection_svc").expose(app)

app.mount("/metrics", metrics)

app.include_router(detection_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8005)
