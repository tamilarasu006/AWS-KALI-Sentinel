import json
import hashlib
from datetime import datetime
from typing import Dict, Any

class ManifestGenerator:
    @staticmethod
    def generate(dataset_id: str, name: str, version: str, category: str, license_info: str,
                 sample_count: int, token_count: int, file_count: int,
                 tokenizer_version: str, processing_version: str, quality_status: str,
                 filepath: str) -> None:
        manifest = {
            "dataset_id": dataset_id,
            "dataset_name": name,
            "version": version,
            "category": category,
            "license": license_info,
            "sample_count": sample_count,
            "token_count": token_count,
            "file_count": file_count,
            "tokenizer_version": tokenizer_version,
            "processing_version": processing_version,
            "quality_status": quality_status,
            "created_at": datetime.utcnow().isoformat()
        }
        manifest_str = json.dumps(manifest, sort_keys=True)
        manifest["checksum"] = hashlib.sha256(manifest_str.encode()).hexdigest()
        
        with open(filepath, "w") as f:
            json.dump(manifest, f, indent=4)
        return manifest
