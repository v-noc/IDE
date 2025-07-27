# src/backend/tests/unit/core/parser/complex_project/config.py

import os
from typing import Dict, Any


DEFAULT_CONFIG = {
    "debug": True,
    "port": 8000,
    "host": "localhost"
}


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from file or return defaults"""
    if os.path.exists(config_path):
        import json
        with open(config_path, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


class ConfigManager:
    def __init__(self):
        self.config = load_config()
        
    def get(self, key: str, default=None):
        return self.config.get(key, default) 