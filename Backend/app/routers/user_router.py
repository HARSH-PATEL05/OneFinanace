from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models,schemas,crud

from app.db import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

router = APIRouter(tags=['Users'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    
    return crud.create_user(db, user)

@router.get("/users/")
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)
