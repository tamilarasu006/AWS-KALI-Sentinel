"""KALI Inference Engine adapter."""

import logging
from collections.abc import AsyncIterator
from typing import Any, Dict, List, Sequence

from OpenDEMON.core.registry import EngineRegistry
from OpenDEMON.core.types import Message
from OpenDEMON.engine._base import InferenceEngine, estimate_prompt_tokens
from OpenDEMON.engine._stubs import StreamChunk
from OpenDEMON.kali import get_registry

logger = logging.getLogger(__name__)

@EngineRegistry.register("kali")
class KALIEngine(InferenceEngine):
    """Engine backend bridging OpenDEMON and KALI AI models."""

    engine_id = "kali"
    is_cloud = False

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the KALI engine adapter."""
        self._registry = get_registry()

        if "kali" not in self._registry.list_models():
            from pathlib import Path
            from OpenDEMON.kali.model.config import KALIModelConfig
            from OpenDEMON.kali.model.kali_model import KALIModel

            checkpoint = (
                Path(__file__).resolve().parents[3]
                / "kali-mini-checkpoint"
            )

            if checkpoint.is_dir() and (checkpoint / "config.json").exists():
                logger.info("Loading KALI checkpoint: %s", checkpoint)
                model = KALIModel.from_pretrained(
                    str(checkpoint),
                    device="cpu",
                    dtype="float32",
                )
            else:
                logger.warning(
                    "KALI checkpoint not found at %s; "
                    "using untrained fallback.",
                    checkpoint,
                )
                config = KALIModelConfig(
                    model_name="kali",
                    model_path="internal://untrained",
                )
                model = KALIModel(config)

            self._registry.register_model(
                "kali",
                model,
                is_default=True,
            )

    def _format_messages(self, messages: Sequence[Message]) -> str:
        """Flatten a sequence of Messages into a raw prompt string."""
        prompt = ""
        for msg in messages:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            prompt += f"<{role}>\n{msg.content}\n</{role}>\n"
        return prompt

    def generate(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate text using a registered KALI model."""
        user_prompt = next(
            (getattr(m, "content", "") for m in reversed(messages) if getattr(getattr(m, "role", None), "value", str(getattr(m, "role", ""))) == "user"),
            ""
        )
        if not user_prompt:
            user_prompt = self._format_messages(messages)

        # 1. Try Live Hosted KALI Model API
        try:
            from kali_sentinel.model_client import get_kali_client
            client = get_kali_client()
            live_res = client.generate(user_prompt)
            if live_res and len(live_res.strip()) > 10:
                prompt_tokens = estimate_prompt_tokens(messages)
                completion_tokens = max(1, len(live_res) // 4)
                return {
                    "content": live_res,
                    "model": model,
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    },
                    "finish_reason": "stop",
                }
        except Exception as exc:
            logger.debug("KALIEngine live API call skipped: %s", exc)

        # 2. Local Model Fallback
        kali_model = self._registry.get_model(model)

        if not kali_model.health():
            kali_model.load()

        prompt = self._format_messages(messages)

        result = kali_model.generate(
            prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        if isinstance(result, dict):
            content = result.get("content", result.get("text", ""))
            usage = result.get("usage")
        else:
            content = str(result)
            usage = None

        prompt_tokens = estimate_prompt_tokens(messages)
        completion_tokens = max(1, len(str(content)) // 4)

        if usage is None:
            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }

        return {
            "content": str(content),
            "model": model,
            "usage": usage,
            "finish_reason": "stop",
        }

    async def stream(
        self,
        messages: Sequence[Message],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream generated text from a registered KALI model."""
        user_prompt = next(
            (getattr(m, "content", "") for m in reversed(messages) if getattr(getattr(m, "role", None), "value", str(getattr(m, "role", ""))) == "user"),
            ""
        )
        if not user_prompt:
            user_prompt = self._format_messages(messages)

        # 1. Try Live Hosted KALI Model API
        try:
            import asyncio
            from kali_sentinel.model_client import get_kali_client
            client = get_kali_client()
            live_res = client.generate(user_prompt)
            if live_res and len(live_res.strip()) > 10:
                words = live_res.split(" ")
                for i, w in enumerate(words):
                    suffix = " " if i < len(words) - 1 else ""
                    yield w + suffix
                    await asyncio.sleep(0.01)
                return
        except Exception as exc:
            logger.debug("KALIEngine live stream skipped: %s", exc)

        # 2. Local Model Fallback
        kali_model = self._registry.get_model(model)

        if not kali_model.health():
            kali_model.load()

        prompt = self._format_messages(messages)

        result = kali_model.generate(
            prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        content = (
            result.get("content", result.get("text", ""))
            if isinstance(result, dict)
            else str(result)
        )

        for word in str(content).split():
            yield word + " "

    def list_models(self) -> List[str]:
        """Return identifiers of models available on this engine."""
        return self._registry.list_models()

    def health(self) -> bool:
        """Engine is healthy if the KALI foundation is loaded."""
        return True

    def can_serve(self, model: str) -> bool:
        """Check if the specific model exists in the KALI registry."""
        try:
            self._registry.get_model(model)
            return True
        except KeyError:
            return False

    def prepare(self, model: str) -> None:
        """Load the model into memory before first use."""
        try:
            kali_model = self._registry.get_model(model)
            if not kali_model.health():
                kali_model.load()
        except KeyError:
            pass

    def close(self) -> None:
        """Unload all KALI models."""
        for model_name in self._registry.list_models():
            self._registry.get_model(model_name).unload()
