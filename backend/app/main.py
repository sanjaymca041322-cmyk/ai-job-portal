from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.candidates.router import router as candidates_router
from app.modules.jobs.router import router as jobs_router
from app.modules.users.router import router as users_router

app = FastAPI(
	title=settings.app_name,
	version=settings.app_version,
)

allowed_origins = [
	"http://127.0.0.1:5173",
	"http://127.0.0.1:5174",
	"http://localhost:5173",
	"http://localhost:5174",
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=allowed_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(candidates_router)
app.include_router(jobs_router)

@app.get("/health")
def health_check() -> dict[str, str]:
	return {"status": "healthy"}