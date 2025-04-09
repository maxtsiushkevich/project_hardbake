from fastapi import APIRouter
from fastapi import HTTPException
import asyncio
from typing import Optional
from pika.exceptions import AMQPError

from api.services.rabbitmq_service import consume_raw_packets, packet_processing_callback

router = APIRouter(prefix="/management", tags=["Management"])

consumer_task: Optional[asyncio.Task] = None


@router.post("/start_consumer/")
async def start_consumer():
    global consumer_task

    if consumer_task is not None and not consumer_task.done():
        return {"status": "Consumer is already running"}

    try:
        consumer_task = asyncio.create_task(run_packet_consumer())
        return {"status": "Packet consumer started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start consumer: {str(e)}")


@router.post("/stop_consumer/")
async def stop_consumer():
    global consumer_task

    if consumer_task is None or consumer_task.done():
        return {"status": "No active consumer to stop"}

    try:
        consumer_task.cancel()
        return {"status": "Packet consumer stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop consumer: {str(e)}")
    finally:
        consumer_task = None


async def run_packet_consumer():
    try:
        try:
            await consume_raw_packets(
                queue_name='sniffer_svc.raw_packets.processor',
                callback=packet_processing_callback
            )
        except AMQPError as e:
            print(f"RabbitMQ error: {e}, attempting to reconnect...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Consumer task was cancelled")
    finally:
        print("Packet consumer stopped")


@router.get("/consumer_status/")
async def get_consumer_status():
    if consumer_task is None:
        return {"status": "not running"}
    elif consumer_task.done():
        return {"status": "stopped", "error": str(consumer_task.exception()) if consumer_task.exception() else None}
    else:
        return {"status": "running"}


# @router.on_event("shutdown")
# async def shutdown_event():
#     global consumer_task, stop_consumer_event
#
#     if consumer_task is not None and not consumer_task.done():
#         stop_consumer_event.set()
#         try:
#             await consumer_task
#         except:
#             pass


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
