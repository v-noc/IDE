# src/backend/tests/unit/core/parser/complex_project/services/data/cache.py

from typing import Any, Optional, Dict
import time


class CacheManager:
    """In-memory cache manager"""
    
    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value with optional TTL"""
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        
        self.cache[key] = {
            "value": value,
            "expiry": expiry
        }
        return True
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if time.time() > entry["expiry"]:
            del self.cache[key]
            return None
        
        return entry["value"]
    
    def delete(self, key: str) -> bool:
        """Delete cache entry"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        return self.get(key) is not None
    
    def size(self) -> int:
        """Get number of cache entries"""
        # Clean expired entries first
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry["expiry"]
        ]
        for key in expired_keys:
            del self.cache[key]
        
        return len(self.cache)


class LRUCache:
    """Least Recently Used cache implementation"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_order: list = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get value and update access order"""
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set value with LRU eviction"""
        if key in self.cache:
            # Update existing
            self.cache[key] = value
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new
            if len(self.cache) >= self.max_size:
                # Evict least recently used
                lru_key = self.access_order.pop(0)
                del self.cache[lru_key]
            
            self.cache[key] = value
            self.access_order.append(key)
    
    def delete(self, key: str) -> bool:
        """Delete entry"""
        if key in self.cache:
            del self.cache[key]
            self.access_order.remove(key)
            return True
        return False 