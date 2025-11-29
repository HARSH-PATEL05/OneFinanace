import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_size=5,        # Keep 5 connections open
    max_overflow=10,
    pool_pre_ping=True, 
    connect_args={"sslmode": "require"} 
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
   
    Base.metadata.create_all(bind=engine)
