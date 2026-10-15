"""KALI AI Inference Engine."""

from ..model.base import KALIModelBase


class KALIInferenceEngine:
    """Core inference engine for KALI models."""

    def __init__(self, model: KALIModelBase):
        self.model = model

    def run(self, prompt: str, **kwargs) -> str:
        """Run the inference engine on a prompt."""
        return self.model.generate(prompt, **kwargs)
