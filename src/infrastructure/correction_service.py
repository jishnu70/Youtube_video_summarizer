# src/infrastructure/correction_service.py

import logging
import os
from functools import lru_cache
from pathlib import Path

import language_tool_python as ltp

logger = logging.getLogger(__name__)

ignore_list = [
    "Java",
    "Python",
    "TensorFlow",
    "Hadoop",
    "Spring",
    "Django",
    "JVM",
    "NASA",
]
replace_dict = {
    "Jawa": "Java",
    "Jaw": "Java",
    "Possum": "Rossum",  # Guido van Rossum
    "Vista": "Guido",  # if Whisper mangles his name
}


class Correction_Service:
    def __init__(
        self,
        lang: str = "en-US",
        ignore_list: list[str] = ignore_list,
        replace_dict: dict[str, str] = replace_dict,
    ) -> None:
        """
        Initialize the correction tool.
        lang: language code (default is English, US).
        """
        logger.info("Initializing Correction_Service with LanguageTool")
        jar_dir = os.getenv("LTP_JAR_DIR_PATH")
        logger.info(f"Using LanguageTool directory: {jar_dir}")

        # Explicitly set the LanguageTool home directory
        if jar_dir:
            p = Path(jar_dir)
            if p.exists():
                logger.info(f"Using LanguageTool directory: {jar_dir}")
                os.environ["LTP_HOME"] = jar_dir
            else:
                logger.warning(
                    f"LTP_JAR_DIR_PATH set but does not exist: {jar_dir}. Falling back to default behavior."
                )
                os.environ.pop("LTP_HOME", None)
        else:
            # Let language_tool_python use its normal cache behavior
            os.environ.pop("LTP_HOME", None)
        try:
            self.tool = ltp.LanguageTool(lang)
            logger.info("Correction_Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LanguageTool: {str(e)}")
            raise RuntimeError(f"LanguageTool initialization failed: {str(e)}")

        self.ignore_list = ignore_list or []
        self.replace_dict = replace_dict or {}

    def clean(self, text: str) -> str:
        """
        Correct spelling and grammar in a given text.
        """
        # Step 1: Apply custom replacements before correction
        for wrong, right in self.replace_dict.items():
            text = text.replace(wrong, right)

        # To Find all issues in the text
        matches = self.tool.check(text)

        # Step 3: Filter out issues that touch ignore words
        filtered_matches = []
        for match in matches:
            if any(word in match.context for word in self.ignore_list):
                continue
            filtered_matches.append(match)

        # Correct the errors
        corrected = ltp.utils.correct(text, filtered_matches)

        return corrected


@lru_cache(maxsize=1)
def get_correction_service() -> Correction_Service:
    """
    Get a cached instance of the Correction_Service.
    """
    return Correction_Service()
