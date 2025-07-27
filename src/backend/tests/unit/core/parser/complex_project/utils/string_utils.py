# src/backend/tests/unit/core/parser/complex_project/utils/string_utils.py

import re
from typing import List


def clean_string(text: str) -> str:
    """Clean and normalize string"""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def split_words(text: str) -> List[str]:
    """Split text into words"""
    cleaned = clean_string(text)
    return cleaned.split()


class StringProcessor:
    """Advanced string processing utility"""
    
    def __init__(self, case_sensitive: bool = True):
        self.case_sensitive = case_sensitive
    
    def process(self, text: str) -> str:
        if not self.case_sensitive:
            text = text.lower()
        return clean_string(text)
    
    def validate_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) 