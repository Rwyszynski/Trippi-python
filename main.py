from fastapi import FastAPI

app = FastAPI(title="TrippiApp API")

@app.get("/health")
def health():
    return {"status": "ok"}