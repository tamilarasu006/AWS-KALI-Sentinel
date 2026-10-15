import os
import torch
import logging
from typing import Dict, Any, Optional
from torch.utils.data import DataLoader
from OpenDEMON.kali.model.kali_model import KALIModel

logger = logging.getLogger(__name__)

class KALITrainer:
    """Native PyTorch training loop for the KALI architecture."""
    
    def __init__(
        self, 
        model: KALIModel, 
        learning_rate: float = 3e-4, 
        weight_decay: float = 0.1,
        gradient_accumulation_steps: int = 1,
        mixed_precision: bool = True
    ):
        self.model = model
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.mixed_precision = mixed_precision
        
        self.device = self.model.config.device
        
        # Optimizer
        self.optimizer = torch.optim.AdamW(
            self.model.transformer.parameters(), 
            lr=self.learning_rate, 
            weight_decay=self.weight_decay
        )
        
        # AMP Scaler
        self.scaler = torch.amp.GradScaler() if self.mixed_precision and "cuda" in self.device else None
        
        self.current_step = 0
        self.current_epoch = 0

    def resume_from_checkpoint(self, checkpoint_dir: str):
        """Resumes optimizer state if available."""
        # The model weights are assumed to be loaded via KALIModel.from_pretrained
        opt_path = os.path.join(checkpoint_dir, "optimizer.pt")
        if os.path.exists(opt_path):
            state = torch.load(opt_path, map_location=self.device)
            self.optimizer.load_state_dict(state["optimizer"])
            self.current_step = state["step"]
            self.current_epoch = state["epoch"]
            logger.info(f"Resumed from step {self.current_step}")

    def save_checkpoint(self, save_directory: str):
        """Saves model and optimizer state."""
        self.model.save_pretrained(save_directory)
        opt_path = os.path.join(save_directory, "optimizer.pt")
        torch.save({
            "optimizer": self.optimizer.state_dict(),
            "step": self.current_step,
            "epoch": self.current_epoch
        }, opt_path)
        logger.info(f"Checkpoint saved to {save_directory}")

    def train_epoch(self, dataloader: DataLoader, pad_token_id: int) -> float:
        """Runs a single training epoch."""
        self.model.transformer.train()
        total_loss = 0.0
        
        loss_fct = torch.nn.CrossEntropyLoss(ignore_index=pad_token_id)
        
        for batch_idx, batch in enumerate(dataloader):
            input_ids = batch["input_ids"].to(self.device)
            labels = batch["labels"].to(self.device)
            
            # Autocast for mixed precision
            device_type = "cuda" if "cuda" in self.device else "cpu"
            with torch.autocast(device_type=device_type, enabled=self.mixed_precision and device_type == "cuda", dtype=torch.float16):
                logits = self.model.transformer(input_ids)
                
                # Shift for next token prediction
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = labels[..., 1:].contiguous()
                
                loss = loss_fct(shift_logits.view(-1, self.model.config.vocab_size), shift_labels.view(-1))
                loss = loss / self.gradient_accumulation_steps
            
            # Backward pass
            if self.scaler is not None:
                self.scaler.scale(loss).backward()
            else:
                loss.backward()
                
            total_loss += loss.item() * self.gradient_accumulation_steps
            
            # Step optimizer
            if (batch_idx + 1) % self.gradient_accumulation_steps == 0:
                if self.scaler is not None:
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    self.optimizer.step()
                    
                self.optimizer.zero_grad()
                self.current_step += 1
                
        self.current_epoch += 1
        return total_loss / max(1, len(dataloader))
