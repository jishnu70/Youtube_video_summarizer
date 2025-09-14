# src/infrastructure/summarizer_service.py

from transformers import pipeline

class SummarizerService:
    def __init__(self, model_name: str = "facebook/bart-large-cnn") -> None:
        """
        Initialize the summarizer with a pretrained model.
        """
        self._summarizer = pipeline("summarization", model_name)

    def summarize(self, text: str, max_length: int=500, min_length: int=200):
        """
        Summarize the given text.
        min_length and max_length control the summary size.
        """
        if not text or len(text.strip()) == 0:
            return ""

        result = self._summarizer(text, min_length=min_length, max_length=max_length, do_sample=False)
        return result[0]["summary_text"]
