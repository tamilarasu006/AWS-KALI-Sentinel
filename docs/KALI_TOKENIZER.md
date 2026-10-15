# KALI Tokenizer Architecture

The KALI Tokenizer replaces the legacy `DummyKALITokenizer` with a production-grade Byte-Pair Encoding (BPE) tokenizer, implemented using the standard HuggingFace `tokenizers` Rust backend.

## Core Features
1. **Subword Encoding:** Uses standard BPE logic to split unknown or large words into frequent subword chunks, drastically reducing vocabulary overhead.
2. **Byte-Level Pre-tokenization:** Encodes strings down to byte representations before applying BPE merging rules. This perfectly handles JSON, URLs, Python code, and Multilingual text without collapsing edge-case characters into `<unk>`.
3. **Special Tokens:** Defines the exact multi-turn chat primitives needed by the KALI instruction tuning pipeline:
   - `<bos>`, `<eos>`, `<pad>`, `<unk>`
   - `<user>`, `<assistant>`, `<tool>`

## Persistence and Configuration
The tokenizer ensures that the explicit `vocab_size` passed into the model constructor is strictly enforced. It exports directly to a single `tokenizer.json` file which defines the merges and the exact vocab mappings. 

```python
from OpenDEMON.kali.tokenizer.bpe_tokenizer import KALIBPETokenizer

# Train/Initialize
tokenizer = KALIBPETokenizer(vocab_size=32000)
tokenizer.save("path/to/tokenizer.json")

# Load existing
loaded = KALIBPETokenizer(vocab_size=32000, tokenizer_path="path/to/tokenizer.json")
```

## Batching and Padding
The tokenizers support `encode_batch` and `decode_batch` for accelerating dataset preparation. If `<bos>` is required, it dynamically inserts the `bos_token_id` to the front of all encoded arrays.
