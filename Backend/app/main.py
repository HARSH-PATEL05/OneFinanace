from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal,Base,engine,create_tables
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from app.routers import user_router
from app.routers.broker_routes import router as broker_router
from app.routers.portfolio_routes import router as portfolio_router


app = FastAPI(
    title="OneFinance",
    description="AI Financial Advisor with all finance of yours",
    version="1.0.0"
)

app.include_router(broker_router)
app.include_router(user_router.router)
app.include_router(portfolio_router)


origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {"message": "Welcome to Universal Broker Integration API"}


@app.on_event("startup")
def startup_event():
    create_tables()

@app.get("/db-status", tags=["System"])
def db_status(db: Session = Depends(lambda: SessionLocal())):
    result = db.execute(text("SELECT current_database();")).fetchone()
    return {"connected_database": result[0]}