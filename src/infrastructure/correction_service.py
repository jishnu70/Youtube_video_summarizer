import language_tool_python as ltp

ignore_list=["Java", "Python", "TensorFlow", "Hadoop", "Spring", "Django", "JVM", "NASA"]
replace_dict={
    "Jawa": "Java",
    "Jaw": "Java",
    "Possum": "Rossum",   # Guido van Rossum
    "Vista": "Guido",     # if Whisper mangles his name
}

class Correction_Service:
    def __init__(
        self,
        lang: str = "en-US",
        ignore_list: list[str]=ignore_list,
        replace_dict: dict[str,str]=replace_dict
    ) -> None:
        """
        Initialize the correction tool.
        lang: language code (default is English, US).
        """
        self.tool = ltp.LanguageTool(lang)
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
