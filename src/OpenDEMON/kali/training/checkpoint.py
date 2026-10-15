import os
import torch
from typing import Dict, Any

class CheckpointManager:
    """Manages saving and resuming training checkpoints."""
    
    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        
    def save(
        self, 
        model: torch.nn.Module, 
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        epoch: int,
        step: int,
        loss: float,
        filename: str = "checkpoint.pt"
    ):
        path = os.path.join(self.save_dir, filename)
        torch.save({
            'epoch': epoch,
            'step': step,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'loss': loss,
        }, path)

    def load(self, path: str, model: torch.nn.Module, optimizer: torch.optim.Optimizer = None, scheduler: Any = None) -> Dict[str, Any]:
        """Loads a checkpoint and returns training metadata."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Checkpoint not found: {path}")
            
        checkpoint = torch.load(path, map_location='cpu')
        model.load_state_dict(checkpoint['model_state_dict'])
        
        if optimizer and 'optimizer_state_dict' in checkpoint:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            
        if scheduler and 'scheduler_state_dict' in checkpoint:
            scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
            
        return {
            'epoch': checkpoint.get('epoch', 0),
            'step': checkpoint.get('step', 0),
            'loss': checkpoint.get('loss', float('inf'))
        }
