import os
import redis.asyncio as redis

def get_redis_connection():
    host = os.getenv("REDIS_HOST")
    port = os.getenv("REDIS_PORT")
    return redis.Redis(host=host, port=int(port), db=0)
