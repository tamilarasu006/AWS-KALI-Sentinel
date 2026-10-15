import hashlib
import json

class VersionControl:
    @staticmethod
    def compute_config_hash(config: dict) -> str:
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
