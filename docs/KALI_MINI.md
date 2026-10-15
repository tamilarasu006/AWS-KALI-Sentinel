# KALI-Mini Model Architecture

`KALI-Mini` is the first scalable incarnation of the core `KALITransformer` network. Built explicitly for localized iteration and rapid training, it maps the foundational layers of the KALI architecture into a lightweight 256-hidden-size matrix footprint.

## Configuration Parameters
The architecture ships natively with the following hyperparameters defined via the `get_kali_mini_config()` factory in `config.py`:
- **Context Length**: 1024 tokens
- **Hidden Size**: 256
- **Num Layers**: 4 Transformer Blocks
- **Attention Heads**: 4 Query Heads
- **KV Heads**: 4 (Supports standard Multi-Head Attention, Grouped-Query configurable)
- **Intermediate Size**: 1024 (SwiGLU Expansion)
- **Vocab Size**: 32,000

## Architecture Pipeline
- **Embedding**: Token Embedding initialized mapped directly to the `vocab_size`.
- **Blocks**: Standard Deep Decoder blocks encapsulating:
  - `RMSNorm` (Pre-norm formulation).
  - `CausalSelfAttention` paired dynamically with Rotary Position Embeddings (`RoPE`).
  - `SwiGLU` Multi-Layer Perceptron.
- **LM Head**: Unbiased Linear layer projecting the 256-dimension space back out to the 32k vocabulary distribution.

## Checkpointing & State Persistence
The model seamlessly interfaces with the HuggingFace-style persistence API natively:
- `save_pretrained(directory)`: Exports `config.json`, `tokenizer.json`, and `pytorch_model.bin`.
- `from_pretrained(directory)`: Re-instantiates the architecture entirely from local disk cache, securely bootstrapping weights via `weights_only=True`.

## Status
*Disclaimer:* `KALI-Mini` acts exclusively as the architectural skeleton. While it structurally supports forward propagation, KV caching, and full backpropagation, it **is not intelligent** until trained on a comprehensive instruction dataset.
