import torch
import torch.nn as nn

class QuantizationConfig:
    def __init__(self, mode: str = "none"):
        self.mode = mode

def apply_dynamic_quantization(model: nn.Module, config: QuantizationConfig) -> nn.Module:
    """
    Applies configurable quantization to the model dynamically.
    Supported modes: 'int8'
    """
    if config.mode == "int8":
        # PyTorch native dynamic quantization for Linear layers
        return torch.quantization.quantize_dynamic(
            model, {nn.Linear}, dtype=torch.qint8
        )
    return model
