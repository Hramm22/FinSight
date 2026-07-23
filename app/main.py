from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.briefing import router as briefing_router


app = FastAPI(
    title="FinSight API",
    description=(
        "경제 뉴스와 국내 주식 시장 데이터를 수집하고, "
        "LangGraph Multi-Agent 구조를 통해 시장 브리핑을 생성하는 API입니다."
    ),
    version="1.0.0",
)


# 프론트엔드와 FastAPI 서버의 통신을 허용하기 위한 CORS 설정
# 개발 단계에서는 localhost를 사용하고,
# 배포 이후에는 실제 프론트엔드 주소를 추가하면 됩니다.
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 브리핑 관련 API 등록
app.include_router(
    briefing_router,
    prefix="/api",
)


@app.get(
    "/",
    tags=["System"],
    summary="FinSight API 기본 정보",
)
def root():
    return {
        "service": "FinSight",
        "description": "AI 기반 국내 금융시장 브리핑 서비스",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "health_check": "/health",
    }


@app.get(
    "/health",
    tags=["System"],
    summary="서버 상태 확인",
)
def health_check():
    return {
        "status": "ok",
        "service": "FinSight",
        "version": "1.0.0",
    }