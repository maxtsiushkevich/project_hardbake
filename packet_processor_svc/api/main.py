from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv

from api.monitoring.prometheus import metrics, instrumentator
from api.repository.redis_repository import RedisConnection
from api.routers.packet_processor import router as packet_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    conn = RedisConnection().connection
    await conn.flushdb()
    yield
    # shutdown


app = FastAPI(lifespan=lifespan, title='Project Hardbake. Packet processor service')

instrumentator.instrument(app, metric_namespace="packet_processor_svc").expose(app)

app.mount("/metrics", metrics)
app.include_router(packet_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8002)
