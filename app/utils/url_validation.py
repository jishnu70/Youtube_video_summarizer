# app/utils/url_validation.py
import logging
import urllib.parse

import httpx
from fastapi import HTTPException

from app.models.schemas import VideoSummaryRequest

logger = logging.getLogger(__name__)


def _safe_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


async def _validate_youtube_url(url: str) -> bool:
    """
    Validate if the provided URL is a valid YouTube video URL.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path  # Keep original casing; YouTube IDs are case-sensitive
    except Exception as e:
        logger.error(f"Error parsing URL: {e}")
        raise HTTPException(status_code=400, detail="Malformed URL structure.")

    # Allow subdomains like m.youtube.com or youtube.com safely
    if not any(
        d == domain or domain.endswith("." + d) for d in ["youtube.com", "youtu.be"]
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL. Please provide a valid YouTube video URL.",
        )

    video_id: str = ""

    if "youtube.com" in domain:
        # Rejects shorts immediately if it's in the path string
        if "/shorts/" in path.lower():
            raise HTTPException(
                status_code=400,
                detail="YouTube Shorts are not supported. Please use a regular video.",
            )

        # Format A: Handles standard watch links (/watch?v=dQw4w9WgXcQ)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if "v" in query_params:
            video_id = query_params["v"][0]

        # Format B: Safe index parsing for embed links (/embed/dQw4w9WgXcQ)
        elif path.lower().startswith(("/embed/", "/v/")):
            path_segments = [seg for seg in path.split("/") if seg]
            if len(path_segments) >= 2:
                video_id = path_segments[1]

    elif "youtu.be" in domain:
        # Format C: Short links (https://youtu.be)
        path_segments = [seg for seg in path.split("/") if seg]
        if path_segments:
            video_id = path_segments[0]

    # Validate that the extracted string is an authentic 11-char YouTube ID token
    if not video_id or len(video_id) != 11:
        raise HTTPException(
            status_code=400,
            detail="Could not extract a valid 11-character YouTube Video ID.",
        )

    # Brute force live availability verification
    async with httpx.AsyncClient() as client:
        try:
            # MUST use client.get() here because YouTube returns 200 OK for dead videos.
            # We need to inspect the response body text.
            response = await client.get(
                _safe_url(video_id), follow_redirects=True, timeout=5
            )
            response.raise_for_status()

            # Inspect the page body for YouTube's visual error string layouts
            page_content = response.text
            if (
                "video-unavailable" in page_content
                or "This video isn't available anymore" in page_content
            ):
                raise HTTPException(
                    status_code=400,
                    detail="The YouTube video does not exist, is private, or has been deleted.",
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to access the URL. HTTP status code: {e.response.status_code}",
            )
        except httpx.RequestError:
            raise HTTPException(
                status_code=400,
                detail="Network error occurred while validating the URL.",
            )

    return True


async def validate_youtube_url(payload: VideoSummaryRequest) -> bool:
    return await _validate_youtube_url(payload.url)
