import asyncio
from fastapi import FastAPI, APIRouter

router = APIRouter(prefix="/management", tags=["Management"])

async def consume():
    """Функция обработки сообщений"""
    pass

@router.post("/start_consumer/")
async def start_consumer():
    """Запуск обработчика сообщений"""
    pass

@router.post("/stop_consumer/")
async def stop_consumer():
    """Остановка обработчика сообщений"""
    pass

@router.get("/")
async def root():
    return {"message": "Use /start_consumer and /stop_consumer"}
