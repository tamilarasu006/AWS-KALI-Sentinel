# KALI Training Architecture

The KALI Training Pipeline provides an end-to-end framework for pretraining and fine-tuning the native `KALIModel` architecture. Built on PyTorch, it implements data loading, scrubbing, sequence packing, and full-precision/mixed-precision backpropagation.

## Modules

### 1. Data Pipeline (`data.py`)
- **Cleaning**: Scrubbing mechanisms strip high-entropy secrets and standard API keys (e.g. `api_key: "..."`) from entering the corpus.
- **Deduplication**: SHA-256 hash sets prevent exact data overlap.
- **Tokenization & Packing**: Converts text to BPE tokens via `KALIBPETokenizer` and chunks them strictly into fixed `context_length` matrices (e.g., 1024 for `KALI-Mini`).

### 2. Trainer Engine (`trainer.py`)
- **PyTorch Loop**: Implements the canonical optimization loop (Forward -> Loss -> Backward -> Step).
- **Optimization**: Uses `AdamW`.
- **AMP**: Automatic Mixed Precision enabled via `torch.amp.GradScaler` for CUDA acceleration.
- **Gradient Accumulation**: Simulated larger batch sizes on constrained hardware.
- **Checkpointing**: Exports and imports `optimizer.pt` in tandem with the native `KALIModel` serialization boundaries.

### 3. Evaluation (`eval.py`)
- Standard tracking for Loss and Perplexity on held-out validation sets.
- Stubs for Tool-Calling benchmarks (JSON validity testing).

### 4. Orchestrator Pipeline (`pipeline.py`)
Encapsulates the multi-stage curriculum:
1. `run_pretraining()`
2. `run_instruction_finetuning()`
3. `run_tool_calling_finetuning()`

## Data Boundaries
The architecture enforces strict segregation:
- **Private Data / User Secrets**: Must NEVER be ingested into the `run_pretraining` calls.
- **Codebase Boundaries**: Do not blindly pass the system's `src/` files into the trainer unless explicitly authorized for code fine-tuning.
