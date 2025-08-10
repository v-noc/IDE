# src/backend/tests/unit/core/parser/sample_project/utils.py

from typing import Optional


def helper_function(i:int, b:Optional[bool]=False)->str:
    """A simple helper function."""
    print("This is a helper.")

class UtilityClass:
    def do_something(self):
        return "done"
