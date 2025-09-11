# src/infrastructure/stt_service.py

from io import BytesIO
import numpy as np
import whisper
import soundfile as sf

class STTService:
    def __init__(self, model_size: str = "small") -> None:
        self.model = whisper.load_model(model_size)

    async def transcribe_audio(self, wav_bytes: BytesIO, chunk_sec: int = 10) -> str:
        """
        Transcribe a WAV BytesIO in chunks.
        chunk_sec: seconds per chunk (not currently implemented for chunking)
        """
        try:
            wav_bytes.seek(0)
            wav_bytes.seek(0, 2)  # Seek to end to get size
            size = wav_bytes.tell()
            wav_bytes.seek(0)  # Reset to beginning
            print(f"[DEBUG] WAV size: {size / 1024:.2f} KB")

            # Read audio file
            audio, sr = sf.read(wav_bytes)
            print(f"[DEBUG] Audio shape: {audio.shape}, Sample rate: {sr}")

            # Convert to numpy array and ensure it's float32
            audio = np.array(audio).astype(np.float32)

            # Convert stereo to mono if necessary
            if len(audio.shape) > 1 and audio.shape[1] > 1:
                print("[DEBUG] Converting stereo to mono")
                audio = np.mean(audio, axis=1)

            # Ensure audio is 1D
            if len(audio.shape) > 1:
                audio = audio.flatten()

            print(f"[DEBUG] Final audio shape: {audio.shape}")

            # Transcribe using Whisper
            print("[DEBUG] Starting transcription...")
            result = self.model.transcribe(
                audio,
                fp16=False,
                language='en',  # Force English
                task='transcribe',  # Specify transcription task
                verbose=True,  # More detailed output
                condition_on_previous_text=False  # Don't condition on previous text
            )
            text = result.get("text", "")
            print("[DEBUG] Transcription completed")
            print(f"[DEBUG] Detected language: {result.get('language', 'unknown')}")

            return text.strip()

        except Exception as e:
            print(f"[ERROR] Transcription failed: {e}")
            return ""
