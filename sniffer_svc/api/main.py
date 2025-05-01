import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routers.sniffer_rmq import router as sniffer_router
from api.repository.redis_repository import RedisConnection
from api.monitoring.prometheus import metrics, instrumentator
from dotenv import load_dotenv

from api.core.context import rabbitmq_client
from fastapi.middleware.cors import CORSMiddleware
from api.core.logger import logger, LOGGING_CONFIG

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = RedisConnection().connection
    await conn.flushdb()
    logger.info('Redis is cleared')
    yield
    await conn.close()


app = FastAPI(lifespan=lifespan, title='Project Hardbake. Sniffer service')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator.instrument(app, metric_namespace="sniffer_svc").expose(app)

app.mount("/metrics", metrics)

app.include_router(sniffer_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000, log_config=LOGGING_CONFIG)
