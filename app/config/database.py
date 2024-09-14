from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.config import settings

# use local environment
engine_url = settings.database_private_url


engine = create_engine(
    engine_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
)



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
