# src/presentation/routes.py

from fastapi.responses import JSONResponse
from src.application.use_case import UseCase
from src.domain.entities import VideoResponse, VideoURL
from fastapi import FastAPI, Depends, Response, status
from typing import Annotated

from src.domain.model_exceptions import FailedToFetch, FailedToSave, InsufficientData, VideoNotAvailableError
from src.presentation.container import get_use_case

app = FastAPI(
    title="Youtube Video Summarizer",
    version="1.2.0",
    description="API using FastAPI to get a summary of a youtube video",
)

@app.exception_handler(VideoNotAvailableError)
async def video_not_found_handler(request, exc):
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

@app.exception_handler(InsufficientData)
async def insufficient_data_handler(request, exc):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

@app.exception_handler(Exception)
async def generic_handler(request, exc):
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Internal server error"})

@app.exception_handler(FailedToFetch)
async def fail_to_fetch_handler(request, exc):
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": str(exc)})

@app.exception_handler(FailedToSave)
async def fail_to_save_handler(request, exc):
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "There is a problem in the connection to the business logic"})

@app.get("/")
def root():
    return Response("Backend is online")

@app.post("/", response_model=VideoResponse|str)
async def get_summary(video: VideoURL, use_case:Annotated[UseCase, Depends(get_use_case)]):
    return await use_case.send(video=video)
