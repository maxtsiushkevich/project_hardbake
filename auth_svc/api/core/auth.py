import os
from authx import AuthX, AuthXConfig
from dotenv import load_dotenv

load_dotenv()

config = AuthXConfig(
    JWT_ALGORITHM="HS256",
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
    JWT_TOKEN_LOCATION=["cookies"],
)

auth = AuthX(config=config)
