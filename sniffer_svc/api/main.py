import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routers.sniffer import router as sniffer_router
from api.routers.interface import router as interface_router
from api.repository.redis_repository import get_redis_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_redis_connection()
    await conn.flushdb()
    yield
    await conn.close()


app = FastAPI(lifespan=lifespan)

app.include_router(sniffer_router)
app.include_router(interface_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
