from fastapi import FastAPI

app = FastAPI(title="FinSight")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "FinSight"
    }