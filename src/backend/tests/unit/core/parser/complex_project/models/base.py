# src/backend/tests/unit/core/parser/complex_project/models/base.py

from typing import Any, Dict, Optional
from datetime import datetime


class BaseModel:
    """Base model class for all data models"""
    
    def __init__(self):
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def update(self, **kwargs):
        """Update model attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()


class ValidationMixin:
    """Mixin for model validation"""
    
    def validate(self) -> bool:
        """Validate model data"""
        return True
    
    def get_errors(self) -> Optional[Dict[str, str]]:
        """Get validation errors"""
        return None 