# main.py

import asyncio
from src.infrastructure.correction_service import Correction_Service
from src.infrastructure.stt_service import STTService
from src.infrastructure.summarizer_service import SummarizerService
from src.infrastructure.yt_service import YoutubeService

yt_service = YoutubeService()
stt_service = STTService(model_size="base")
c_service = Correction_Service()
s_service = SummarizerService()

async def test_stream():
    # url = "https://www.youtube.com/watch?v=x7X9w_GIm1s"
    url = "https://www.youtube.com/watch?v=l9AzO1FMgM8"

    print("Downloading audio...")
    chunks = await yt_service.download(url)
    print("Transcribing...")
    transcription = await stt_service.transcribe_audio(chunks)
    print("\n--- RAW Transcription ---\n")
    print(transcription)
    corrected_transcription = c_service.clean(transcription)
    print("\n--- Corrected Transcription ---\n")
    print(corrected_transcription)
    summary = s_service.summarize(corrected_transcription)
    print("\n--- Final Output ---\n")
    print("Summary:\n", summary)

asyncio.run(test_stream())
