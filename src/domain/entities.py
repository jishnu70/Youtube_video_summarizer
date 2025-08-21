# src/domain/entities.py

from typing import Optional
from pydantic import BaseModel

class VideoURL(BaseModel):
    id: Optional[str]
    url: str

class VideoResponse(VideoURL):
    transcript: str
    summary: Optional[str] = None
