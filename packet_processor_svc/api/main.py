from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.monitoring.prometheus import metrics, instrumentator
from api.repository.redis_repository import RedisConnection
from api.routers.management_router import router as management_router
from api.routers.pcap_processor import router as packet_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    conn = RedisConnection().connection
    await conn.flushdb()
    yield
    # shutdown


app = FastAPI(lifespan=lifespan, title='Project Hardbake. Packet processor service')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator.instrument(app, metric_namespace="packet_processor_svc").expose(app)

app.mount("/metrics", metrics)
app.include_router(packet_router)
app.include_router(management_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8002)
