# src/infrastructure/yt_service.py

import json
from typing import AsyncGenerator
from io import BytesIO
import aiohttp
from typing import Optional
import yt_dlp
import requests
from src.domain.model_exceptions import VideoNotAvailableError

class YoutubeService:
    def __init__(self, chunk_duration_ms: int = 120_000) -> None:
        self.chunk_duration_ms = chunk_duration_ms

    def __captions_to_text(self, captions_text: str) -> Optional[str]:
        """
        Convert YouTube captions JSON to plain text.
        """
        if not captions_text:
            return None

        try:
            captions_json = json.loads(captions_text)
        except json.JSONDecodeError:
            return None
        events = captions_json.get("events", [])
        text_segments = []
        for event in events:
            for seg in event.get("segs", []):
                if "utf8" in seg:
                    text_segments.append(seg["utf8"].replace("\n", " "))
        return " ".join(text_segments)

    def download_captions(self, url: str, lang: str = "en")->Optional[str]:
        """
        Download captions text if available.
        Returns text or None if captions are not available.
        """
        ydl_opts = {"skip_download": True, "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            captions = info.get("subtitles") or info.get("automatic_captions")
            if captions is None:
                return None

            # Find first language that starts with lang_prefix
            subtitle_key = next((k for k in captions if k.startswith(lang)), None)
            if not subtitle_key:
                return None
            # Take first available format
            formats = captions[subtitle_key]
            if not formats or "url" not in formats[0]:
                return None

            subtitle_url = formats[0]["url"]
            response = requests.get(subtitle_url)
            if response.status_code != 200:
                return None

            captions_text = response.text
            return self.__captions_to_text(captions_text)

    async def stream_audio_chunks(self, url: str) -> AsyncGenerator[BytesIO, None]:
        """
        Streams YouTube audio asynchronously in WAV format, yielding chunks.
        """
        ydl_opts = {
            "format": "bestaudio/best",
            "skip_download": True,
            "quiet": True,
            "nocheckcertificate": True,
            "geo_bypass": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url=url, download=False)
            audio_url = info.get("url")

            if audio_url is None:
                raise VideoNotAvailableError("Incorrect URL or video does not exists")

        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"Failed to fetch audio, status {resp.status}")
                chunk_size = int(16000 * self.chunk_duration_ms / 1000)
                async for data in resp.content.iter_chunked(chunk_size):
                    yield BytesIO(data)
