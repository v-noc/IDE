# src/backend/tests/unit/core/parser/complex_project/main.py

# Absolute imports
import os
import sys
from typing import Dict, List, Optional
import json as JSON

# Relative imports
from . import config
from .utils import math_utils, string_utils
from .models.user import User, UserType
from .services.auth import AuthService
from .services.data.database import DatabaseManager

# Aliased imports
from .utils.math_utils import calculate as calc
from .models import user as user_mod
import logging as log

# Circular import (will test error handling)
from .circular_dep import CircularClass


class Application:
    def __init__(self, name: str):
        self.name = name
        self.db = DatabaseManager()
        self.auth = AuthService()
        self.users: List[User] = []
        self.config = config.load_config()
        
    def start(self):
        """Start the application"""
        log.info(f"Starting {self.name}")
        result = calc(10, 20)
        user = User(name="test", user_type=UserType.ADMIN)
        self.users.append(user)
        
    def process_data(self, data: Dict) -> Optional[str]:
        """Process some data"""
        processed = string_utils.clean_string(data.get("text", ""))
        return JSON.dumps({"processed": processed})


def main():
    """Main entry point"""
    app = Application("TestApp")
    app.start()
    return app


if __name__ == "__main__":
    main() 