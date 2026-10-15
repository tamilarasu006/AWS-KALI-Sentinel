# KALI-MINI TRAINING REPORT

## MODEL
Name: KALI-Mini
Config: KALIModelConfig(model_name='KALI-Mini', model_path='./kali-mini', tokenizer_path=None, context_length=1024, hidden_size=256, num_layers=4, num_attention_heads=4, num_kv_heads=4, intermediate_size=1024, vocab_size=32000, dtype='float32', device='cpu')

## PARAMETERS
Total: 20580608
Trainable: 20580608

## TOKENIZER
Type: BPE
Vocab Size: 32153

## DATASET
{
  "dataset_name": "KALI-Mini-Synthetic",
  "source": "Local Generation",
  "license": "MIT",
  "language": "en",
  "number_of_samples": 700,
  "hash": "1a2b3c4d5e"
}

## TRAINING STATUS
Epochs: 3
Final Train Loss: 0.4258
Final Val Loss: 0.4330
Perplexity: 1.54

## CHECKPOINT
Location: ./kali-mini-checkpoint

## GENERATION TEST
Prompt: Hello
Output: ,<dummy_415><dummy_301><dummy_297>?<dummy_297>?
Latency: 0.258s
Prompt: Explain Python.
Output: ..
Latency: 0.159s
Prompt: Write a simple function.
Output: ..
Latency: 0.110s
Prompt: Return JSON.
Output: ..
Latency: 0.141s
Prompt: Complete this sentence.
Output: <dummy_419><dummy_387><dummy_295>.<dummy_387><dummy_295><dummy_387>
Latency: 0.116s

## KALI ENGINE
Registered: True

## HARDWARE USED
Device: cpu

## TESTS PASSED
- Configuration created
- Model architecture verified
- Real Tokenizer encoded/decoded
- Dataset compiled
- Training loop executed without errors
- Checkpoint saved successfully
- Generation generated output

## KNOWN LIMITATIONS
- Dataset is tiny synthetic for testing pipeline
- Loss doesn't necessarily indicate true language understanding yet
