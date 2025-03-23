import uvicorn
from fastapi import FastAPI
from api.monitoring.prometheus import metrics, instrumentator
from dotenv import load_dotenv
from api.routers.interface import router as interface_router

load_dotenv()

app = FastAPI(title='Project Hardbake. System Information service')

instrumentator.instrument(app, metric_namespace="system_info_svc").expose(app)

app.mount("/metrics", metrics)

app.include_router(interface_router)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)
