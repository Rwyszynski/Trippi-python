from fastapi import FastAPI
from database import engine, Base
from router import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TrippiApp - Chat Service",
    description="Konwersacje i wiadomości",
    version="1.0.0",
)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "chat-service"}