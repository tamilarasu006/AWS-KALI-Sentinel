import torch
import logging
from typing import Any
from .lora import LoRAFinetuner
from .config import KALISFTConfig as FinetuneConfig

try:
    from transformers import BitsAndBytesConfig
except ImportError:
    BitsAndBytesConfig = None

try:
    from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
except ImportError:
    prepare_model_for_kbit_training = None
    LoraConfig = None
    get_peft_model = None

logger = logging.getLogger(__name__)

class QLoRAFinetuner(LoRAFinetuner):
    """Handles Quantized LoRA (QLoRA) fine-tuning."""

    def load_base_model(self, model_class: Any, model_name_or_path: str, **kwargs):
        """Loads the base model in 4-bit precision."""
        if BitsAndBytesConfig is None:
            raise ImportError("transformers and bitsandbytes are required for QLoRA.")
            
        logger.info(f"Loading base model from {model_name_or_path} in 4-bit precision")
        
        quant_config = BitsAndBytesConfig(
            load_in_4bit=self.config.use_4bit,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        
        self.base_model = model_class.from_pretrained(
            model_name_or_path,
            quantization_config=quant_config,
            device_map="auto",
            **kwargs
        )
        
        # Enable gradient checkpointing and prepare for kbit training
        self.base_model.gradient_checkpointing_enable()
        if prepare_model_for_kbit_training:
            self.base_model = prepare_model_for_kbit_training(self.base_model)
            
    def prepare_adapter(self):
        """Injects QLoRA adapters."""
        if get_peft_model is None:
            raise ImportError("PEFT library is required.")
            
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
