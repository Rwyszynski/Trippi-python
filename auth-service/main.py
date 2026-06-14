from fastapi import FastAPI
from database import engine, Base
from router import router
from keys import generate_keys

generate_keys()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TrippiApp - Auth Service",
    description="Rejestracja, logowanie, JWT",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth-service"}