# src/backend/tests/unit/core/parser/complex_project/circular_dep.py

# This creates a circular import with main.py for testing purposes
from .models.user import User


class CircularClass:
    """Class that creates circular dependency"""
    
    def __init__(self):
        self.user = User(name="circular")
    
    def get_application(self):
        # This would create a circular import if main.py tries to import this
        from .main import Application
        return Application("circular") 