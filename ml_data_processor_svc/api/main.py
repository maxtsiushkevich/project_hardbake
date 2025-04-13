from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from api.monitoring.prometheus import metrics, instrumentator
from api.routers.management import router as management_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(lifespan=lifespan, title='Project Hardbake. ML Data Processor service')

instrumentator.instrument(app, metric_namespace="ml_data_processor_svc").expose(app)

app.mount("/metrics", metrics)

app.include_router(management_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8003)
