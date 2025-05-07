import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.logger import LOGGING_CONFIG, logger
from api.core.roles import Role
from api.services.users import create_user
from api.utils.database import SessionLocal, engine, Base
from api.schemas.schemas import UserCreate
from api.models.models import User
from api.routes.router import router as auth_router

app = FastAPI(title='Project Hardbake. Auth Service')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

Base.metadata.create_all(bind=engine)


def create_initial_admin():
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin_user = UserCreate(
                username="admin",
                password="admin",
                role=Role.ADMIN
            )
            create_user(db=db, user=admin_user)
            logger.info("Initial admin user created successfully")
    finally:
        db.close()


create_initial_admin()

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8008, log_config=LOGGING_CONFIG)
