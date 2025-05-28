from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, workspaces, surveys, assessment, dashboard, reports, files
import uvicorn

app = FastAPI(title="Survey Backend API", version="1.0.0")

# CORS 설정
origins = [
    "http://localhost:3000",      # React 개발 서버
    "http://localhost:5173",      # Vite 개발 서버
    "http://localhost",
    "http://3.35.230.242",
    "http://3.35.230.242:3000",
    "http://3.35.230.242:8080",
    "http://3.35.230.242:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["Workspaces"])
app.include_router(surveys.router, prefix="/api/v1/surveys", tags=["Surveys"])
app.include_router(assessment.router, prefix="/api/v1/assessment", tags=["Assessment"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Survey Backend API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True) 