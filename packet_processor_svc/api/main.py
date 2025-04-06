from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from api.monitoring.prometheus import metrics, instrumentator
from dotenv import load_dotenv
from api.routers.packet_processor import router as packet_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(title='Project Hardbake. Packet processor service')

instrumentator.instrument(app, metric_namespace="packet_processor_svc").expose(app)

app.mount("/metrics", metrics)
app.include_router(packet_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8002)
