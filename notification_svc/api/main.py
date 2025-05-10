from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from api.core.logger import LOGGING_CONFIG
from api.monitoring.prometheus import metrics, instrumentator
from api.routers.notification_router import router as notification_router
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(lifespan=lifespan, title='Project Hardbake. Notification Service')



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator.instrument(app, metric_namespace="notification_svc").expose(app)

app.mount("/metrics", metrics)

app.include_router(notification_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8006, log_config=LOGGING_CONFIG)
