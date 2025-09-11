# src/infrastructure/yt_service.py

import json
from io import BytesIO
import asyncio
from typing import Optional
import yt_dlp
import requests

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

    # async def download_audio_as_wav(self, url: str) -> BytesIO:
    #     """
    #     Download audio from YouTube and convert to WAV format (mono, 16kHz for Whisper).
    #     """

    #     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
    #         temp_path = temp_file.name

    #     try:
    #         # Download and convert audio directly to WAV using yt-dlp
    #         process = await asyncio.create_subprocess_exec(
    #             "yt-dlp",
    #             "-f", "bestaudio/best",
    #             "--extract-audio",
    #             "--audio-format", "wav",
    #             "--audio-quality", "0",  # Best quality
    #             "--postprocessor-args", "ffmpeg:-ac 1 -ar 16000",  # Mono, 16kHz
    #             "-o", temp_path.replace('.wav', '.%(ext)s'),
    #             url,
    #             stdout=asyncio.subprocess.PIPE,
    #             stderr=asyncio.subprocess.PIPE,
    #         )
    #         stdout, stderr = await process.wait()

    #         if process.returncode != 0:
    #             print(f"[ERROR] yt-dlp failed: {stderr.decode()}")
    #             raise RuntimeError(f"yt-dlp failed with return code {process.returncode}")

    #         wav_bytes = BytesIO()
    #         with open(temp_path, 'rb') as f:
    #             wav_bytes.write(f.read())

    #         wav_bytes.seek(0)
    #         return wav_bytes
    #     finally:
    #         # Clean up temporary file
    #         if os.path.exists(temp_path):
    #             os.unlink(temp_path)
    #         # Also clean up the actual output file (yt-dlp adds .wav extension)
    #         actual_output = temp_path.replace('.wav', '.wav')
    #         if os.path.exists(actual_output):
    #             os.unlink(actual_output)


    async def download(self, url: str):
        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "-o", "-",
            "--extract-audio",
            "--audio-format", "wav",
            url,
        ]
        # First, get the raw audio stream
        process = await asyncio.create_subprocess_exec(
            "yt-dlp", "-f", "bestaudio/best", "-o", "-", "--extract-audio", "--audio-format", "wav", url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Then pipe it to ffmpeg for conversion to wav
        ffmpeg_process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-i", "pipe:0", "-ar", "16000", "-ac", "1", "-f", "wav", "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async def pump(reader, writer):
            try:
                while True:
                    chunk = await reader.read(4096)
                    if not chunk:
                        break
                    writer.write(chunk)
                    await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()

        pump_task = asyncio.create_task(pump(process.stdout, ffmpeg_process.stdin))

        wav_bytes = BytesIO()
        while True:
            chunk = await ffmpeg_process.stdout.read(4096)
            if not chunk:
                break
            wav_bytes.write(chunk)

        await pump_task
        await process.wait()
        await ffmpeg_process.wait()
        wav_bytes.seek(0)
        return wav_bytes
