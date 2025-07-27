# src/backend/tests/unit/core/parser/complex_project/utils/math_utils.py

from typing import Union
import math


def calculate(a: Union[int, float], b: Union[int, float]) -> float:
    """Calculate sum of two numbers"""
    return float(a + b)


def factorial(n: int) -> int:
    """Calculate factorial of n"""
    if n <= 1:
        return 1
    return n * factorial(n - 1)


class MathCalculator:
    """Advanced mathematical calculator"""
    
    def __init__(self):
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result
    
    def power(self, base: float, exp: float) -> float:
        result = math.pow(base, exp)
        self.history.append(f"power({base}, {exp}) = {result}")
        return result
    
    def get_history(self):
        return self.history.copy() 