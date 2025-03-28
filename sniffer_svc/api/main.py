import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routers.sniffer_rmq import router as sniffer_router
from api.repository.redis_repository import RedisConnection
from api.monitoring.prometheus import metrics, instrumentator
from dotenv import load_dotenv

from api.core.context import rabbitmq_client

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = RedisConnection().connection
    await conn.flushdb()
    yield
    await conn.close()
    await rabbitmq_client.close_connection()


app = FastAPI(lifespan=lifespan, title='Project Hardbake. Sniffer service')

instrumentator.instrument(app, metric_namespace="sniffer_svc").expose(app)

app.mount("/metrics", metrics)

app.include_router(sniffer_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
