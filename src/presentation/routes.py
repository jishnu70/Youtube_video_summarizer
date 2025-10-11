from src.application.use_case import UseCase
from src.domain.entities import VideoResponse, VideoURL
from fastapi import FastAPI, Depends, Response
from typing import Annotated

from src.presentation.container import get_use_case

app = FastAPI(
    title="Youtube Video Summarizer",
    version="1.1.0",
    description="API using FastAPI to get a summary of a youtube video",
)

@app.get("/")
def root():
    return Response("Backend is online")

@app.post("/", response_model=VideoResponse)
async def get_summary(url: VideoURL, use_case:Annotated[UseCase, Depends(get_use_case)]):
    return await use_case.send(url=url)
