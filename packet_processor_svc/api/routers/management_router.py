from fastapi import APIRouter, HTTPException
import asyncio
import logging
from typing import Optional
from starlette import status

from api.services.proxy_packet_processor import ProxyPacketProcessor

router = APIRouter(prefix="/management", tags=["Management"])

consumer_task: Optional[asyncio.Task] = None
proxy_packet_processor = ProxyPacketProcessor()


@router.post("/start_consumer/")
async def start_consumer():
    global consumer_task

    if consumer_task and not consumer_task.done():
        return {"status": "Consumer is already running"}

    try:
        consumer_task = asyncio.create_task(
            proxy_packet_processor.start_consuming(
                callback=proxy_packet_processor.packet_processing_callback
            )
        )
        return {"status": "Packet consumer started successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start consumer: {str(e)}"
        )


@router.post("/stop_consumer/")
async def stop_consumer():
    global consumer_task

    if not consumer_task or consumer_task.done():
        return {"status": "No active consumer to stop"}

    try:
        consumer_task.cancel()
        try:
            await asyncio.wait_for(consumer_task, timeout=5)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logging.warning("Consumer task did not cancel gracefully within timeout")

        return {"status": "Packet consumer stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop consumer: {str(e)}"
        )
    finally:
        consumer_task = None


@router.get("/consumer_status/")
async def get_consumer_status():
    if not consumer_task:
        return {"status": "not running"}
    elif consumer_task.done():
        return {
            "status": "stopped",
            "error": str(consumer_task.exception()) if consumer_task.exception() else None
        }
    else:
        return {"status": "running"}


@router.get("/")
async def root():
    return {
        "message": "Packet processing service",
        "endpoints": {
            "start_consumer": "/start_consumer/",
            "stop_consumer": "/stop_consumer/",
            "consumer_status": "/consumer_status/"
        }
    }
