import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.routes.router import router
from app.service.maintenance import TaskMaintenanceService


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    maintenance_service = TaskMaintenanceService()
    await maintenance_service.requeue_stuck_tasks(stale_after=timedelta(seconds=30))

    async def maintenance_loop() -> None:
        while True:
            await asyncio.sleep(300)
            await maintenance_service.requeue_stuck_tasks()

    maintenance_task = asyncio.create_task(maintenance_loop())
    try:
        yield
    finally:
        maintenance_task.cancel()
        try:
            await maintenance_task
        except asyncio.CancelledError:
            pass
        await close_db()


app = FastAPI(
    title="Youtube Video Summarizer API",
    description="An API that summarizes YouTube videos.",
    version="0.0.1",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"message": "API is working!"}
