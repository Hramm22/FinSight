from fastapi import FastAPI

from app.api.briefing import router as briefing_router

app = FastAPI(title="FinSight")

app.include_router(briefing_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "FinSight",
    }