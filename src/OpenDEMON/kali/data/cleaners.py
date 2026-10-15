import re
import unicodedata

def clean_text(text: str, preserve_code_formatting: bool = False) -> str:
    """
    Cleans raw text data.
    - Normalizes unicode.
    - Removes zero-width characters and invalid unicode.
    - Normalizes whitespace (if not preserving code formatting).
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'[​‌‍﻿\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    if not preserve_code_formatting:
        text = re.sub(r'[ 	]+', ' ', text)
        return text.strip()
    return text

def remove_html_boilerplate(text: str) -> str:
    # simple heuristic for removing common boilerplate, but retaining structure
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    return clean_text(text, preserve_code_formatting=False)
