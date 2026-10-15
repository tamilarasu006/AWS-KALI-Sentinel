import os
import torch
import logging
from typing import Any, Dict, Optional
from .config import KALISFTConfig as FinetuneConfig

try:
    from peft import LoraConfig, get_peft_model, PeftModel
except ImportError:
    LoraConfig = None
    get_peft_model = None
    PeftModel = None

logger = logging.getLogger(__name__)

class LoRAFinetuner:
    """Handles standard LoRA fine-tuning for KALI models."""
    
    def __init__(self, config: FinetuneConfig):
        self.config = config
        self.model = None
        self.base_model = None

    def load_base_model(self, model_class: Any, model_name_or_path: str, **kwargs):
        """Loads the base transformer model."""
        logger.info(f"Loading base model from {model_name_or_path}")
        self.base_model = model_class.from_pretrained(
            model_name_or_path,
            torch_dtype=torch.float16,
            device_map="auto",
            **kwargs
        )

    def prepare_adapter(self):
        """Injects LoRA adapters into the base model."""
        if get_peft_model is None:
            raise ImportError("PEFT library is required for LoRA fine-tuning.")
            
        if self.base_model is None:
            raise ValueError("Base model must be loaded before preparing adapter.")
            
        lora_config = LoraConfig(
            r=self.config.rank,
            lora_alpha=self.config.alpha,
            target_modules=self.config.target_modules,
            lora_dropout=self.config.dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )
        self.model = get_peft_model(self.base_model, lora_config)
        self.model.print_trainable_parameters()

    def train_step(self, batch: Dict[str, torch.Tensor], optimizer: torch.optim.Optimizer) -> float:
        """Runs a single training step."""
        if self.model is None:
            raise ValueError("Model with adapters is not prepared.")
            
        self.model.train()
        outputs = self.model(**batch)
        loss = outputs.loss / self.config.gradient_accumulation_steps
        loss.backward()
        return loss.item()

    def save_adapter(self, output_dir: str):
        """Saves only the LoRA adapter weights."""
        if self.model is None:
            raise ValueError("Model is not initialized.")
        os.makedirs(output_dir, exist_ok=True)
        self.model.save_pretrained(output_dir)
        logger.info(f"Saved LoRA adapter to {output_dir}")

    def load_adapter(self, adapter_path: str):
        """Loads a previously trained adapter onto the base model."""
        if PeftModel is None:
            raise ImportError("PEFT library is required.")
        if self.base_model is None:
            raise ValueError("Base model must be loaded before loading adapter.")
            
        self.model = PeftModel.from_pretrained(self.base_model, adapter_path)
        logger.info(f"Loaded LoRA adapter from {adapter_path}")

    def evaluate_adapter(self, batch: Dict[str, torch.Tensor]) -> float:
        """Evaluates the model on a validation batch."""
        if self.model is None:
            raise ValueError("Model is not initialized.")
            
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(**batch)
            return outputs.loss.item()

    def merge_adapter(self):
        """Merges the adapter weights into the base model explicitly."""
        if self.model is None:
            raise ValueError("Model is not initialized.")
        logger.info("Merging LoRA adapter weights into base model...")
        self.base_model = self.model.merge_and_unload()
        self.model = self.base_model
