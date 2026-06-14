from fastapi import FastAPI
from database import engine, Base
from router import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TrippiApp - User Service",
    description="Zarządzanie użytkownikami",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "user-service"}