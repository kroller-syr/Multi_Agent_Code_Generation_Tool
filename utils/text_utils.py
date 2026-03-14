import re

def strip_code_fences(text: str) -> str:
    """Remove triple-backtick fences if the model returns them."""
    if not text:
        return ""
    # Remove ```python ... ``` or ``` ... ```
    text = re.sub(r"^```(?:python)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())
    return text.strip()