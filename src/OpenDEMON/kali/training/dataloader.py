import torch
from torch.utils.data import DataLoader, random_split
from typing import Tuple
from .dataset import KALIDataset

def create_dataloaders(
    dataset: KALIDataset,
    batch_size: int,
    val_split: float = 0.05,
    seed: int = 42,
    num_workers: int = 4
) -> Tuple[DataLoader, DataLoader]:
    """
    Creates train and validation DataLoaders.
    """
    generator = torch.Generator().manual_seed(seed)
    
    val_size = int(len(dataset) * val_split)
    train_size = len(dataset) - val_size
    
    train_dataset, val_dataset = random_split(
        dataset, [train_size, val_size], generator=generator
    )
    
    train_loader = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, val_loader
