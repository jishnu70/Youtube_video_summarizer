# main.py

import asyncio
from src.infrastructure.stt_service import STTService
from src.infrastructure.yt_service import YoutubeService

yt_service = YoutubeService()
stt_service = STTService(model_size="base")

async def test_stream():
    # url = "https://www.youtube.com/watch?v=x7X9w_GIm1s"
    url = "https://www.youtube.com/watch?v=l9AzO1FMgM8"

    print("Downloading audio...")
    chunks = await yt_service.download(url)
    print("Transcribing...")
    transcription = await stt_service.transcribe_audio(chunks)
    print("\n--- Transcription ---\n")
    print(transcription)

asyncio.run(test_stream())
