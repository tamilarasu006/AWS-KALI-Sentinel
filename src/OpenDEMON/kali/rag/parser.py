import re
from typing import Dict, Any, Tuple

class DocumentParser:
    """Parses and cleans raw document text."""

    @classmethod
    def parse(cls, raw_text: str, source: str = "") -> Tuple[str, Dict[str, Any]]:
        """
        Cleans text and extracts top-level metadata.
        Returns the cleaned text and any parsed metadata.
        """
        if not raw_text:
            return "", {"source": source}

        cleaned = cls._clean_text(raw_text)
        metadata = {"source": source, "length": len(cleaned)}

        return cleaned, metadata

    @classmethod
    def _clean_text(cls, text: str) -> str:
        """Removes excessive whitespace and unprintable characters."""
        # Replace multiple newlines with double newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove trailing/leading whitespace per line
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()
