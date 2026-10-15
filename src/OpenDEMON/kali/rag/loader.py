from typing import Optional, Any
from pathlib import Path
import json

class DocumentLoader:
    """Loads documents from various file formats."""

    @classmethod
    def load(cls, file_path: str) -> str:
        """Loads a file into a raw text representation."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()

        if ext == ".pdf":
            return cls._load_pdf(path)
        elif ext == ".json":
            return cls._load_json(path)
        elif ext == ".jsonl":
            return cls._load_jsonl(path)
        else:
            # Fallback to plain text for .txt, .md, etc.
            return cls._load_text(path)

    @classmethod
    def _load_text(cls, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")

    @classmethod
    def _load_pdf(cls, path: Path) -> str:
        try:
            import pdfplumber
        except ImportError:
            raise ImportError(
                "PDF support requires pdfplumber. Please install it."
            ) from None

        pages = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n\n".join(pages)

    @classmethod
    def _load_json(cls, path: Path) -> str:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)

    @classmethod
    def _load_jsonl(cls, path: Path) -> str:
        lines = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        parsed = json.loads(line)
                        lines.append(json.dumps(parsed))
                    except json.JSONDecodeError:
                        lines.append(line.strip())
        return "\n".join(lines)
