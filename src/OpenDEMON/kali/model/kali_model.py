"""KALI Model Implementation."""

import torch
from typing import Any, Dict, Iterator

from .base import KALIModelBase
from OpenDEMON.kali.architecture.transformer import KALITransformer
from OpenDEMON.kali.inference.generate import generate_text
from OpenDEMON.kali.inference.streaming import stream_text
from OpenDEMON.kali.tokenizer import DummyKALITokenizer
from OpenDEMON.kali.tokenizer.bpe_tokenizer import KALIBPETokenizer
from OpenDEMON.kali.model.config import KALIModelConfig
import os
import json

class KALIModel(KALIModelBase):
    """Reference implementation of a KALI AI Model."""

    def __init__(self, config):
        super().__init__(config)
        self._is_loaded = False
        self.transformer = None
        self.tokenizer = None

    def load(self) -> None:
        """Load the KALI model from its configured checkpoint."""
        import time
        import logging
        from OpenDEMON.kali.orchestration.metrics import MetricsCollector

        start_t = time.time()

        if self._is_loaded:
            return

        model_path = self.config.model_path

        # Real local checkpoint
        if (
            model_path
            and not model_path.startswith("internal://")
            and os.path.isdir(model_path)
            and os.path.isfile(os.path.join(model_path, "config.json"))
        ):
            loaded = KALIModel.from_pretrained(
                model_path,
                device=self.config.device,
                dtype=self.config.dtype,
            )

            self.transformer = loaded.transformer
            self.tokenizer = loaded.tokenizer
            self._is_loaded = True

            load_time = (time.time() - start_t) * 1000
            MetricsCollector().metrics.model_load_time_ms = load_time
            return

        # Explicit placeholder/testing model only.
        self.tokenizer = DummyKALITokenizer(
            vocab_size=self.config.vocab_size
        )

        if self.tokenizer.vocab_size() != self.config.vocab_size:
            raise ValueError(
                f"Tokenizer vocab size ({self.tokenizer.vocab_size()}) "
                f"does not match model config ({self.config.vocab_size})"
            )

        self.transformer = KALITransformer(self.config)
        self.transformer.to(self.config.device)
        self.transformer.eval()

        if hasattr(torch, "compile") and torch.cuda.is_available():
            try:
                self.transformer = torch.compile(self.transformer)
            except Exception as e:
                logging.getLogger("DEMON.kali").warning(
                    f"torch.compile failed, falling back to eager mode: {e}"
                )

        self._is_loaded = True

        load_time = (time.time() - start_t) * 1000
        MetricsCollector().metrics.model_load_time_ms = load_time

    def unload(self) -> None:
        """Unload model weights from memory safely."""
        import gc
        self._is_loaded = False
        self.transformer = None
        self.tokenizer = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        if not self._is_loaded:
            raise RuntimeError("Model is not loaded.")
        
        return generate_text(
            model=self.transformer,
            prompt=prompt,
            tokenizer=self.tokenizer,
            max_new_tokens=kwargs.get("max_new_tokens", 50),
            temperature=kwargs.get("temperature", 1.0),
            top_k=kwargs.get("top_k", 0),
            top_p=kwargs.get("top_p", 1.0),
            repetition_penalty=kwargs.get("repetition_penalty", 1.0),
            stop_tokens=kwargs.get("stop_tokens", None),
            seed=kwargs.get("seed", None),
        )

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream generated text from prompt."""
        if not self._is_loaded:
            raise RuntimeError("Model is not loaded.")
            
        return stream_text(
            model=self.transformer,
            prompt=prompt,
            tokenizer=self.tokenizer,
            max_new_tokens=kwargs.get("max_new_tokens", 50),
            temperature=kwargs.get("temperature", 1.0),
            top_k=kwargs.get("top_k", 0),
            top_p=kwargs.get("top_p", 1.0),
            repetition_penalty=kwargs.get("repetition_penalty", 1.0),
            stop_tokens=kwargs.get("stop_tokens", None),
            seed=kwargs.get("seed", None),
        )

    def health(self) -> bool:
        """Check health status."""
        return self._is_loaded

    def metadata(self) -> Dict[str, Any]:
        """Return model metadata."""
        return {
            "name": self.config.model_name,
            "path": self.config.model_path,
            "device": self.config.device,
            "dtype": self.config.dtype,
            "loaded": self._is_loaded,
            "architecture": {
                "context_length": self.config.context_length,
                "hidden_size": self.config.hidden_size,
                "num_layers": self.config.num_layers,
                "num_attention_heads": self.config.num_attention_heads,
                "num_kv_heads": self.config.num_kv_heads,
                "intermediate_size": self.config.intermediate_size,
                "vocab_size": self.config.vocab_size
            }
        }

    def count_parameters(self) -> Dict[str, int]:
        """Count trainable and total parameters."""
        if not self._is_loaded or self.transformer is None:
            return {"total": 0, "trainable": 0}
        
        total = sum(p.numel() for p in self.transformer.parameters())
        trainable = sum(p.numel() for p in self.transformer.parameters() if p.requires_grad)
        return {"total": total, "trainable": trainable}

    def save_pretrained(self, save_directory: str):
        """Save model configuration and weights."""
        if not self._is_loaded or self.transformer is None:
            raise RuntimeError("Cannot save an unloaded model.")
            
        os.makedirs(save_directory, exist_ok=True)
        
        # Save config
        config_dict = {
            "model_name": self.config.model_name,
            "context_length": self.config.context_length,
            "hidden_size": self.config.hidden_size,
            "num_layers": self.config.num_layers,
            "num_attention_heads": self.config.num_attention_heads,
            "num_kv_heads": self.config.num_kv_heads,
            "intermediate_size": self.config.intermediate_size,
            "vocab_size": self.config.vocab_size,
            "dtype": self.config.dtype
        }
        config_path = os.path.join(save_directory, "config.json")
        with open(config_path, "w") as f:
            json.dump(config_dict, f, indent=2)
            
        # Save state dict
        model_path = os.path.join(save_directory, "pytorch_model.bin")
        # Unwrap from torch.compile if needed
        model_to_save = self.transformer
        if hasattr(model_to_save, "_orig_mod"):
            model_to_save = model_to_save._orig_mod
            
        torch.save(model_to_save.state_dict(), model_path)
        
        # Save tokenizer if we have the real one
        if isinstance(self.tokenizer, KALIBPETokenizer):
            self.tokenizer.save(os.path.join(save_directory, "tokenizer.json"))

    @classmethod
    def from_pretrained(cls, save_directory: str, device="cpu", dtype="float32"):
        """Load model configuration and weights."""
        config_path = os.path.join(save_directory, "config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config not found at {config_path}")
            
        with open(config_path, "r") as f:
            config_dict = json.load(f)
            
        config = KALIModelConfig(
            model_name=config_dict.get("model_name", "KALI-Loaded"),
            model_path=save_directory,
            context_length=config_dict["context_length"],
            hidden_size=config_dict["hidden_size"],
            num_layers=config_dict["num_layers"],
            num_attention_heads=config_dict["num_attention_heads"],
            num_kv_heads=config_dict["num_kv_heads"],
            intermediate_size=config_dict["intermediate_size"],
            vocab_size=config_dict["vocab_size"],
            device=device,
            dtype=dtype
        )
        
        model = cls(config)
        # Manually load the transformer
        model.transformer = KALITransformer(config)
        
        model_path = os.path.join(save_directory, "pytorch_model.bin")
        if os.path.exists(model_path):
            state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
            model.transformer.load_state_dict(state_dict)
            
        model.transformer.to(device)
        model.transformer.eval()
        
        # Load Tokenizer
        tokenizer_path = os.path.join(save_directory, "tokenizer.json")
        if os.path.exists(tokenizer_path):
            model.tokenizer = KALIBPETokenizer(vocab_size=config.vocab_size, tokenizer_path=tokenizer_path)
        else:
            model.tokenizer = DummyKALITokenizer(vocab_size=config.vocab_size)
            
        model._is_loaded = True
        return model
