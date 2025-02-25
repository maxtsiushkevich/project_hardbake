from fastapi import FastAPI
from api.routers.sniffer import router as sniffer_router
from api.routers.interface import router as interface_router

app = FastAPI()

app.include_router(sniffer_router)
app.include_router(interface_router)