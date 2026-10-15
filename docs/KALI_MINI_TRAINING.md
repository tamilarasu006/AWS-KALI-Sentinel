# KALI-Mini Training Guide

## Architecture
The KALI-Mini model uses a small variant of the `KALITransformer` architecture optimized for local development and testing.
- `context_length`: 1024
- `hidden_size`: 256
- `num_layers`: 4
- `num_attention_heads`: 4
- `num_kv_heads`: 4
- `vocab_size`: 32000

## Configuration
The model configuration is defined in `OpenDEMON.kali.model.config.get_kali_mini_config()`. The configuration is saved alongside the model weights inside `config.json` when a checkpoint is written.

## Dataset Format
The training loop utilizes the `KALIDataset`, which expects pre-tokenized sequences represented as lists of integers.
Each batch consists of `input_ids` and shifted `labels` for Causal Language Modeling next-token prediction.

## Training Command
To train the model natively without breaking out to another script, you can run the pipeline entrypoint:
```bash
python scripts/train_kali_mini.py
```
This script handles tokenizer fitting, dataset manifest generation, training, validation, and evaluation.

## Resume Command
The `KALITrainer` natively supports resuming from checkpoints.
```python
trainer.resume_from_checkpoint("./kali-mini-checkpoint")
```

## Evaluation Command
Evaluation is built into the training loop and prints training/validation loss at each epoch, along with perplexity.

## Checkpoint Location
By default, the pipeline saves model weights (`pytorch_model.bin`), the configuration (`config.json`), the optimizer state (`optimizer.pt`), and the tokenizer (`tokenizer.json`) to:
`./kali-mini-checkpoint`

## Inference Command
The trained model can be used for text generation instantly:
```python
model = KALIModel.from_pretrained("./kali-mini-checkpoint")
output = model.generate("Hello, KALI", max_new_tokens=20)
print(output)
```

## Hardware Requirements
- CPU: Usable (takes ~25 seconds per epoch on a minimal 1000-sample synthetic dataset).
- GPU: Recommended (CUDA with float16 Mixed Precision natively supported via `torch.amp.GradScaler`).

## Known Limitations
- The current pre-training dataset is entirely synthetic and small, designed primarily to validate that the pipeline (tokenizer -> embedding -> transformer -> LM head -> optimizer) works end-to-end without shape/dimension errors.
- As a result, the model output (generation) is primarily "dummy" tokens and gibberish, which is expected for 20M parameters trained on repetitive synthetic data for only a minute.
- Real intelligence requires massive datasets, scaled compute, and extensive RLHF/instruction-tuning phases.
