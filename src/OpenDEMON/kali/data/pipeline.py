import os
import json
from .cleaners import clean_text
from .dedup import Deduplicator
from .filters import SecurityFilter, QualityFilter
from .formats import DataParser
from .splits import DatasetSplitter
from .manifest import ManifestGenerator
from .versioning import VersionControl
from OpenDEMON.kali.tokenizer.tokenizer import KALITokenizer

class DatasetPipeline:
    """
    Orchestrates the entire dataset engineering pipeline for Phase 47.
    """
    def __init__(self, config: dict):
        self.config = config
        self.dedup = Deduplicator()
        self.security = SecurityFilter()
        self.quality = QualityFilter()
        try:
            self.tokenizer = KALITokenizer()
        except:
            self.tokenizer = None
        
        self.stats = {
            "input_samples": 0,
            "output_samples": 0,
            "removed_samples": 0,
            "duplicate_samples": 0,
            "secret_detected_samples": 0,
            "token_count": 0,
            "languages": {},
            "categories": {},
            "splits": {"train": 0, "val": 0, "test": 0}
        }
        
    def process_file(self, file_path: str, format_type: str, category: str, preserve_code: bool = False):
        if format_type == "jsonl":
            iterator = DataParser.parse_jsonl(file_path)
        elif format_type == "json":
            iterator = DataParser.parse_json(file_path)
        elif format_type == "csv":
            iterator = DataParser.parse_csv(file_path)
        elif format_type == "conversation":
            iterator = DataParser.parse_conversation(file_path)
        elif format_type == "instruction":
            iterator = DataParser.parse_instruction(file_path)
        elif format_type == "tool":
            iterator = DataParser.parse_tool_calling(file_path)
        else:
            iterator = DataParser.parse_text(file_path)
            
        processed = []
        for text in iterator:
            self.stats["input_samples"] += 1
            
            cleaned = clean_text(text, preserve_code_formatting=preserve_code)
            if not self.quality.is_quality_sample(cleaned):
                self.stats["removed_samples"] += 1
                continue
                
            if self.security.contains_sensitive_data(cleaned):
                self.stats["secret_detected_samples"] += 1
                continue
                
            if self.dedup.is_duplicate(cleaned):
                self.stats["duplicate_samples"] += 1
                continue
                
            if self.tokenizer:
                tokens = self.tokenizer.encode(cleaned)
                self.stats["token_count"] += len(tokens)
            
            processed.append(cleaned)
            self.stats["output_samples"] += 1
            
        return processed
        
    def generate_report(self, output_path: str):
        report = {
            "pipeline_status": "SUCCESS",
            "stats": self.stats,
            "config_hash": VersionControl.compute_config_hash(self.config)
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=4)
        
        md_report = f"""# KALI Dataset Engineering Report
## Status: SUCCESS
- Input Samples: {self.stats['input_samples']}
- Output Samples: {self.stats['output_samples']}
- Removed (Quality): {self.stats['removed_samples']}
- Removed (Duplicates): {self.stats['duplicate_samples']}
- Removed (Secrets): {self.stats['secret_detected_samples']}
- Total Tokens: {self.stats['token_count']}
"""
        docs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(output_path)))), "docs")
        os.makedirs(docs_path, exist_ok=True)
        with open(os.path.join(docs_path, "KALI_DATASET_ENGINEERING.md"), "w") as f:
            f.write(md_report)
