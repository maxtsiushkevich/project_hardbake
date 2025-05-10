from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from api.core.logger import logger

SQLALCHEMY_DATABASE_URL = "sqlite:///./data.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

@contextmanager
def get_db():
    logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
        logger.debug("Database session yielded successfully")
    except Exception as e:
        logger.error(f"Error occurred while using database session: {e}")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")