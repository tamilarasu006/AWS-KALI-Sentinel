# KALI SFT Documentation

## Architecture
The SFT implementation uses the `KALIMini` architecture (transformer) natively. It implements supervised fine-tuning by optimizing the negative log-likelihood loss for next-token prediction specifically over assistant responses.

## Dataset Format
The data format normalizes conversations into `SFTDataset` by utilizing `KALIChatTemplate`. The internal representation represents conversational turns as `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]` resolving into a standardized byte-stream with role delimitations (`<USER>\n...`). 

## Chat Template
`KALIChatTemplate` strictly handles encoding, decoding, validation, and layout logic. Hardcoded conversation markers are absent from inference logic, entirely centralized in this template. 

## Loss Masking
During the training loop, `SFTDataset` systematically flags input tokens stemming from `system` and `user` messages with a label of `-100`. This ensures gradient descent strictly optimizes the ability to generate the *assistant's response* rather than learning to predict user inputs. 

## Training Configuration
Parameters are explicitly parameterized in `KALISFTConfig`, encompassing:
- Learning Rate
- Batch Size
- Epochs
- Target Modules (for LoRA)
- Checkpointing intervals

## LoRA & QLoRA Configuration
LoRA uses `LoRAFinetuner` via `peft` with configurable rank, alpha, and target_modules. `QLoRAFinetuner` enables 4-bit NormalFloat training (QLoRA) utilizing `bitsandbytes`. Both decouple adapter states from frozen base weights, keeping checkpoints tiny.

## Checkpoint Format
Checkpoints serialize:
- `pytorch_model.bin` (Transformer weights)
- `sft_config.json` (Configuration state)
- Dataset manifest/metrics (`baseline_results.json`, `sft_results.json`)

## Evaluation
Evaluation leverages `SFTTrainer.evaluate` before and after training against a static test dataset, measuring evaluation loss and perplexity. Generative responses to benchmark prompts are written into `generation_results.json`.

## Inference
The KALI API routing engine remains structurally identical. The new model identifies as `kali-mini-sft` within the `KALIModelRegistry`, retaining the previous identifiers safely for A/B testing and rollbacks.

## Known Limitations
- Extreme context lengths (>8k) during SFT will OOM on small local accelerators without deepspeed optimizations.
- Evaluation metrics are currently basic next-token perplexity and raw generative logging, lacking an automated LLM-as-a-judge suite.
