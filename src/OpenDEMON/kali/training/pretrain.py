import torch
import random
import numpy as np
import logging
from typing import List
from .dataset import KALIDataset
from .dataloader import create_dataloaders
from .trainer import Trainer
from .checkpoint import CheckpointManager
from .scheduler import get_cosine_schedule_with_warmup

logger = logging.getLogger(__name__)

def set_seed(seed: int = 42):
    """Sets deterministic seed."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def run_pretraining(
    model: torch.nn.Module,
    train_data: List[List[int]],
    batch_size: int = 8,
    epochs: int = 3,
    lr: float = 5e-5,
    weight_decay: float = 0.01,
    warmup_steps: int = 100,
    seed: int = 42,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
    checkpoint_dir: str = "./checkpoints",
):
    """
    Main entry point for pretraining jobs.
    """
    set_seed(seed)
    
    # Dataset and DataLoaders
    dataset = KALIDataset(train_data)
    train_loader, val_loader = create_dataloaders(dataset, batch_size=batch_size, seed=seed)
    
    # Optimizer
    # Exclude layer norm and bias from weight decay
    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {
            "params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)],
            "weight_decay": weight_decay,
        },
        {
            "params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
            "weight_decay": 0.0,
        },
    ]
    optimizer = torch.optim.AdamW(optimizer_grouped_parameters, lr=lr)
    
    # Scheduler
    total_steps = len(train_loader) * epochs
    scheduler = get_cosine_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        mixed_precision=torch.cuda.is_available()
    )
    
    checkpoint_manager = CheckpointManager(checkpoint_dir)
    
    # Training Loop
    for epoch in range(epochs):
        logger.info(f"Starting Epoch {epoch+1}/{epochs}")
        train_loss = trainer.train_epoch(train_loader, epoch)
        val_loss = trainer.evaluate(val_loader)
        
        logger.info(f"Epoch {epoch+1} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")
        
        checkpoint_manager.save(
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
            epoch=epoch,
            step=(epoch + 1) * len(train_loader),
            loss=val_loss,
            filename=f"checkpoint_epoch_{epoch+1}.pt"
        )
        
    logger.info("Pretraining completed.")
