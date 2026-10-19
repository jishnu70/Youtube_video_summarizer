from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import close_db, init_db
from app.models import *
from app.routes.router import router

# from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Youtube Video Summarizer API",
    description="An API that summarizes YouTube videos.",
    version="0.0.1",
    lifespan=lifespan,
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.include_router(router)


@app.get("/health")
def health_check():
    return {"message": "API is working!"}
