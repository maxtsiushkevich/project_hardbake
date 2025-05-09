from authx import AuthX, AuthXConfig

from api.core.logger import logger

with open("private_key.pem", "r") as f:
    logger.info("Private key loaded")
    PRIVATE_KEY = f.read()

with open("public_key.pem", "r") as f:
    logger.info("Public key loaded")
    PUBLIC_KEY = f.read()

config = AuthXConfig(
    JWT_ALGORITHM="ES256",
    JWT_PRIVATE_KEY=PRIVATE_KEY,
    JWT_PUBLIC_KEY=PUBLIC_KEY,
    JWT_TOKEN_LOCATION=["cookies"],
)
auth = AuthX(config=config)
